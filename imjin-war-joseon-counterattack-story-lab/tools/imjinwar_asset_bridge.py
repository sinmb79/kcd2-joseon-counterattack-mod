#!/usr/bin/env python
"""Private local asset bridge for the installed ImjinWar client.

This script intentionally writes extracted assets only to ignored private
folders or to the local KCD2 Mods directory. Do not commit its generated output.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys
import zipfile


ASSET_FILES = (
    "IMClient/ImjinWar_Data/resources.assets",
    "IMClient/ImjinWar_Data/sharedassets0.assets",
    "IMClient/ImjinWar_Data/globalgamemanagers.assets",
)

DEFAULT_PATTERNS = (
    "Logo",
    "IMJIN",
    "KR_",
    "Kr_",
    "Splash",
    "Sword",
    "House",
    "Door",
    "fire",
    "smoke",
    "slash",
    "Water",
)

PRIVATE_UI_MAP = (
    {
        "source": "Logo_TitleScreen",
        "target": "Libs/UI/Textures/Books/Unique/roses_book_01_ui.dds",
        "size": (1024, 1024),
        "background": (18, 15, 10, 255),
    },
    {
        "source": "Splash",
        "target": "Libs/UI/Textures/Books/Maps/treasureHunter_map1_1_ui.dds",
        "size": (1024, 1024),
        "background": (10, 12, 14, 255),
    },
    {
        "source": "Atlas_IMJIN_Window_32bit",
        "target": "Libs/UI/Textures/Apse/modal_dialog_simple.dds",
        "size": (512, 1024),
        "background": (12, 10, 8, 255),
    },
    {
        "source": "KR_S_Sword_00_D",
        "target": "Libs/UI/Textures/Books/Products/replaceme_ui.dds",
        "size": (256, 256),
        "background": (20, 18, 14, 255),
    },
    {
        "source": "Kr_House_Door_01_D",
        "target": "Libs/UI/Textures/Books/Recipes/replaceme_ui.dds",
        "size": (1024, 1024),
        "background": (18, 14, 10, 255),
    },
    {
        "source": "fx_fire_59a",
        "target": "Libs/UI/Textures/Apse/buff_disks.dds",
        "size": (128, 128),
        "background": (0, 0, 0, 0),
    },
)


def safe_name(value: str, fallback: str) -> str:
    value = value.strip() or fallback
    value = re.sub(r"[^A-Za-z0-9_.@ -]+", "_", value)
    value = value.strip(" .")
    return value or fallback


def import_unitypy():
    try:
        import UnityPy  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "UnityPy is not available. Run kcd2_mod/scripts/build_private_imjinwar_bridge.ps1 first."
        ) from exc
    return UnityPy


def iter_unity_objects(source_root: Path):
    UnityPy = import_unitypy()
    for relative in ASSET_FILES:
        path = source_root / relative
        if not path.exists():
            continue
        env = UnityPy.load(str(path))
        for obj in env.objects:
            yield relative, obj


def collect_manifest(source_root: Path) -> list[dict]:
    rows: list[dict] = []
    for relative, obj in iter_unity_objects(source_root):
        record = {
            "asset_file": relative,
            "type": obj.type.name,
            "path_id": obj.path_id,
        }
        if obj.type.name in {"Texture2D", "Sprite", "TextAsset", "Mesh", "Material"}:
            try:
                data = obj.read()
                record["name"] = getattr(data, "m_Name", "")
                if obj.type.name == "Texture2D":
                    record["width"] = getattr(data, "m_Width", 0)
                    record["height"] = getattr(data, "m_Height", 0)
                    record["format"] = str(getattr(data, "m_TextureFormat", ""))
            except Exception as exc:  # pragma: no cover - defensive for stripped Unity objects
                record["error"] = str(exc)
        rows.append(record)
    return rows


def matches_patterns(name: str, patterns: tuple[str, ...]) -> bool:
    folded = name.lower()
    return any(pattern.lower() in folded for pattern in patterns)


def image_by_name(source_root: Path, wanted: str):
    for relative, obj in iter_unity_objects(source_root):
        if obj.type.name != "Texture2D":
            continue
        data = obj.read()
        name = getattr(data, "m_Name", "")
        if name == wanted:
            image = data.image.convert("RGBA")
            return image, {
                "asset_file": relative,
                "path_id": obj.path_id,
                "name": name,
                "width": getattr(data, "m_Width", 0),
                "height": getattr(data, "m_Height", 0),
                "format": str(getattr(data, "m_TextureFormat", "")),
            }
    raise KeyError(f"Texture not found: {wanted}")


def fit_image(image, size: tuple[int, int], background: tuple[int, int, int, int]):
    from PIL import Image

    target = Image.new("RGBA", size, background)
    source = image.copy()
    source.thumbnail(size, Image.Resampling.LANCZOS)
    x = (size[0] - source.width) // 2
    y = (size[1] - source.height) // 2
    target.alpha_composite(source, (x, y))
    return target


def extract_private_assets(source_root: Path, output_root: Path, patterns: tuple[str, ...]) -> list[dict]:
    textures_dir = output_root / "textures"
    text_dir = output_root / "textassets"
    textures_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    extracted: list[dict] = []
    for relative, obj in iter_unity_objects(source_root):
        if obj.type.name == "Texture2D":
            data = obj.read()
            name = getattr(data, "m_Name", "")
            if not matches_patterns(name, patterns):
                continue
            width = getattr(data, "m_Width", 0)
            height = getattr(data, "m_Height", 0)
            if width <= 0 or height <= 0:
                continue
            filename = safe_name(name, f"texture_{obj.path_id}") + ".png"
            out_path = textures_dir / filename
            data.image.save(out_path)
            extracted.append(
                {
                    "kind": "texture",
                    "name": name,
                    "asset_file": relative,
                    "path_id": obj.path_id,
                    "width": width,
                    "height": height,
                    "private_path": str(out_path),
                }
            )
        elif obj.type.name == "TextAsset":
            data = obj.read()
            name = getattr(data, "m_Name", "")
            if not name.startswith("text_"):
                continue
            raw = getattr(data, "m_Script", b"")
            if isinstance(raw, str):
                payload = raw.encode("utf-8", errors="replace")
            else:
                payload = bytes(raw)
            out_path = text_dir / (safe_name(name, f"text_{obj.path_id}") + f"_{obj.path_id}.txt")
            out_path.write_bytes(payload)
            extracted.append(
                {
                    "kind": "textasset",
                    "name": name,
                    "asset_file": relative,
                    "path_id": obj.path_id,
                    "bytes": len(payload),
                    "private_path": str(out_path),
                }
            )
    return extracted


def build_private_kcd2_ui_pak(source_root: Path, output_root: Path, kcd2_mod_root: Path) -> dict:
    stage_root = output_root / "kcd2_private_ui_stage"
    if stage_root.exists():
        shutil.rmtree(stage_root)
    stage_root.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    for mapping in PRIVATE_UI_MAP:
        image, source_meta = image_by_name(source_root, mapping["source"])
        target_image = fit_image(image, mapping["size"], mapping["background"])
        staged_path = stage_root / mapping["target"]
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        target_image.save(staged_path)
        entries.append(
            {
                "source": source_meta,
                "target": mapping["target"],
                "size": list(mapping["size"]),
                "staged_path": str(staged_path),
            }
        )

    data_dir = kcd2_mod_root / "Data"
    data_dir.mkdir(parents=True, exist_ok=True)
    pak_path = data_dir / "joseon_counterattack_private_ui.pak"
    if pak_path.exists():
        pak_path.unlink()

    with zipfile.ZipFile(pak_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for staged_file in stage_root.rglob("*"):
            if staged_file.is_file():
                archive.write(staged_file, staged_file.relative_to(stage_root).as_posix())

    return {
        "pak_path": str(pak_path),
        "entry_count": len(entries),
        "entries": entries,
        "note": "This private PAK contains locally extracted ImjinWar-derived UI textures and must not be committed or redistributed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=r"C:\Program Files (x86)\Joycity\ImjinWar")
    parser.add_argument("--output", required=True)
    parser.add_argument("--kcd2-mod-root")
    parser.add_argument("--build-ui-pak", action="store_true")
    parser.add_argument("--pattern", action="append", default=[])
    args = parser.parse_args()

    source_root = Path(args.source)
    output_root = Path(args.output)
    if not source_root.exists():
        raise SystemExit(f"ImjinWar source folder was not found: {source_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    patterns = tuple(args.pattern) if args.pattern else DEFAULT_PATTERNS
    manifest = collect_manifest(source_root)
    extracted = extract_private_assets(source_root, output_root, patterns)
    result: dict = {
        "status": "ok",
        "source_root": str(source_root),
        "output_root": str(output_root),
        "unitypy": True,
        "manifest_count": len(manifest),
        "extracted_count": len(extracted),
        "patterns": list(patterns),
    }

    (output_root / "unity_asset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_root / "extracted_private_manifest.json").write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if args.build_ui_pak:
        if not args.kcd2_mod_root:
            raise SystemExit("--kcd2-mod-root is required with --build-ui-pak")
        result["private_kcd2_ui_pak"] = build_private_kcd2_ui_pak(
            source_root,
            output_root,
            Path(args.kcd2_mod_root),
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
