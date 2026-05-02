#!/usr/bin/env python
"""Build a local-only Joseon visual pack for the KCD2 fan mod.

The generated PAK is intentionally private. It can reuse locally extracted
ImjinWar textures as references/composites, then expands them with original
procedural Joseon-style UI, item icons, codex art, and city material overrides.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps


Color = tuple[int, int, int, int]


@dataclass(frozen=True)
class AssetSpec:
    target: str
    size: tuple[int, int]
    generator: str
    label: str


UI_SPECS: tuple[AssetSpec, ...] = (
    AssetSpec("Libs/UI/Textures/Apse/modal_dialog_simple.dds", (512, 1024), "panel", "apse_modal_joseon_window"),
    AssetSpec("Libs/UI/Textures/Apse/info_panel_dark.dds", (1024, 512), "panel_dark", "apse_dark_command_panel"),
    AssetSpec("Libs/UI/Textures/Apse/info_panel_inv.dds", (1024, 512), "panel_inventory", "apse_inventory_panel"),
    AssetSpec("Libs/UI/Textures/Apse/item.dds", (256, 256), "icon_sword", "apse_item_sword"),
    AssetSpec("Libs/UI/Textures/Apse/item_info.dds", (1024, 512), "item_info", "apse_item_info"),
    AssetSpec("Libs/UI/Textures/Apse/item_selection.dds", (1024, 1024), "icon_sheet", "apse_item_selection_sheet"),
    AssetSpec("Libs/UI/Textures/Apse/item_selection_ornament.dds", (1024, 256), "ornament", "apse_item_selection_ornament"),
    AssetSpec("Libs/UI/Textures/Apse/list.dds", (1024, 512), "paper_list", "apse_list_paper"),
    AssetSpec("Libs/UI/Textures/Apse/quest_area.dds", (256, 256), "icon_beacon", "apse_quest_beacon"),
    AssetSpec("Libs/UI/Textures/Apse/character_slot.dds", (512, 512), "character_slot", "apse_character_slot"),
    AssetSpec("Libs/UI/Textures/Apse/character_slot_icons.dds", (512, 256), "small_icon_sheet", "apse_character_slot_icons"),
    AssetSpec("Libs/UI/Textures/Apse/outfit_shields.dds", (512, 256), "shield_strip", "apse_outfit_shields"),
    AssetSpec("Libs/UI/Textures/Apse/reputation.dds", (256, 256), "seal", "apse_reputation_seal"),
    AssetSpec("Libs/UI/Textures/Apse/buff_disks.dds", (256, 256), "buff_disks", "apse_buff_fire_disks"),
    AssetSpec("Libs/UI/Textures/Apse/attack_mode.dds", (512, 256), "attack_mode", "apse_land_battle_attack"),
    AssetSpec("Libs/UI/Textures/Apse/bottom_ornament.dds", (1024, 128), "ornament", "apse_bottom_ornament"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s1_first_ui.dds", (1024, 1024), "city_gate", "codex_city_gate"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s1_p1_left_ui.dds", (1024, 1024), "city_alley", "codex_city_alley"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s1_p1_right_ui.dds", (1024, 1024), "city_market", "codex_city_market"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s2_first_ui.dds", (1024, 1024), "fort_beacon", "codex_beacon_fort"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s2_p1_left_ui.dds", (1024, 1024), "city_wall", "codex_city_wall"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t1_s2_p1_right_ui.dds", (1024, 1024), "paper_list", "codex_campaign_paper"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t2_s1_first_ui.dds", (1024, 1024), "city_gate_night", "codex_city_gate_night"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t2_s1_p1_left_ui.dds", (1024, 1024), "map", "codex_land_map_left"),
    AssetSpec("Libs/UI/Textures/Books/Decorations/t2_s1_p1_right_ui.dds", (1024, 1024), "fort_beacon", "codex_land_map_right"),
    AssetSpec("Libs/UI/Textures/Books/Maps/treasureHunter_map1_1_ui.dds", (1024, 1024), "map", "map_busanjin_supply_1"),
    AssetSpec("Libs/UI/Textures/Books/Maps/treasureHunter_map1_2_ui.dds", (1024, 1024), "map_routes", "map_busanjin_supply_2"),
    AssetSpec("Libs/UI/Textures/Books/Maps/treasureHunter_map2_1_ui.dds", (1024, 1024), "map_fort", "map_dongnae_fort_1"),
    AssetSpec("Libs/UI/Textures/Books/Maps/treasureHunter_map2_2_ui.dds", (1024, 1024), "map_routes", "map_dongnae_fort_2"),
    AssetSpec("Libs/UI/Textures/Books/Products/replaceme_ui.dds", (512, 512), "icon_sword", "product_hwando"),
    AssetSpec("Libs/UI/Textures/Books/Products/1_ui.dds", (512, 512), "icon_sword", "product_front_sword"),
    AssetSpec("Libs/UI/Textures/Books/Products/2_ui.dds", (512, 512), "icon_bow", "product_beacon_bow"),
    AssetSpec("Libs/UI/Textures/Books/Products/3_ui.dds", (512, 512), "icon_shield", "product_gate_shield"),
    AssetSpec("Libs/UI/Textures/Books/Products/4_ui.dds", (512, 512), "icon_dispatch", "product_secret_order"),
    AssetSpec("Libs/UI/Textures/Books/Products/5_ui.dds", (512, 512), "icon_ration", "product_ration"),
    AssetSpec("Libs/UI/Textures/Books/Products/6_ui.dds", (512, 512), "icon_beacon", "product_beacon_fire"),
    AssetSpec("Libs/UI/Textures/Books/Recipes/replaceme_ui.dds", (1024, 1024), "recipe_page", "recipe_campaign_formula"),
    AssetSpec("Libs/UI/Textures/Books/Ingredients/saltpeter_ui.dds", (512, 512), "icon_powder", "ingredient_powder"),
    AssetSpec("Libs/UI/Textures/Books/Ingredients/special_charcoal_ui.dds", (512, 512), "icon_charcoal", "ingredient_charcoal"),
    AssetSpec("Libs/UI/Textures/Books/Ingredients/special_attire_ui.dds", (512, 512), "icon_armor", "ingredient_uniform"),
    AssetSpec("Libs/UI/Textures/Books/Ingredients/honey_ui.dds", (512, 512), "icon_medicine", "ingredient_field_medicine"),
    AssetSpec("Libs/UI/Textures/Books/Unique/roses_book_01_ui.dds", (1024, 1024), "city_gate", "unique_first_city"),
    AssetSpec("Libs/UI/Textures/Books/Unique/roses_book_02_ui.dds", (1024, 1024), "seal_document", "unique_command_seal"),
    AssetSpec("Libs/UI/Textures/Books/Unique/sigismund_seal_ui.dds", (512, 512), "seal", "unique_joseon_seal"),
)


CITY_TEXTURE_SPECS: tuple[AssetSpec, ...] = (
    AssetSpec("Textures/structures/walls/plaster/plaster_a_2x2_diff.dds", (1024, 1024), "hanok_plaster", "city_hanok_plaster_a"),
    AssetSpec("Textures/structures/walls/plaster/plaster_b_1x1_diff.dds", (1024, 1024), "hanok_plaster_beams", "city_hanok_plaster_beams"),
    AssetSpec("Textures/structures/walls/plaster/plaster_d_4x4_diff.dds", (1024, 1024), "hanok_plaster_cracked", "city_hanok_plaster_cracked"),
    AssetSpec("Textures/structures/walls/stone_wall/brick_wall_a_2x2_diff.dds", (1024, 1024), "joseon_stone", "city_joseon_stone_brick"),
    AssetSpec("Textures/structures/walls/stone_wall/stone_wall_a_4x4_diff.dds", (1024, 1024), "joseon_stone", "city_joseon_stone_wall_a"),
    AssetSpec("Textures/structures/walls/stone_wall/stone_wall_c_4x4_diff.dds", (1024, 1024), "joseon_stone_moss", "city_joseon_stone_moss"),
    AssetSpec("Textures/structures/wood/planks_a_rustic_4x4_diff.dds", (1024, 1024), "joseon_gate_wood", "city_joseon_gate_wood_a"),
    AssetSpec("Textures/structures/wood/planks_c_overlap_rustic_2x2_diff.dds", (1024, 1024), "joseon_gate_wood_dark", "city_joseon_gate_wood_dark"),
    AssetSpec("Textures/structures/wood/wooden_beams_01_diff.dds", (1024, 1024), "joseon_beams", "city_joseon_beams"),
    AssetSpec("Textures/structures/window/glass_diamond_window_1x1_diff.dds", (1024, 1024), "hanji_window", "city_hanji_window"),
)


ASSET_SPECS: tuple[AssetSpec, ...] = UI_SPECS + CITY_TEXTURE_SPECS
TRANSPARENT_GENERATORS = {"ornament", "shield_strip", "buff_disks", "seal"}
SAFE_TARGETS = {
    "Libs/UI/Textures/Apse/buff_disks.dds",
    "Libs/UI/Textures/Books/Maps/treasureHunter_map1_1_ui.dds",
    "Libs/UI/Textures/Books/Maps/treasureHunter_map1_2_ui.dds",
    "Libs/UI/Textures/Books/Maps/treasureHunter_map2_1_ui.dds",
    "Libs/UI/Textures/Books/Maps/treasureHunter_map2_2_ui.dds",
    "Libs/UI/Textures/Books/Products/replaceme_ui.dds",
    "Libs/UI/Textures/Books/Products/1_ui.dds",
    "Libs/UI/Textures/Books/Products/2_ui.dds",
    "Libs/UI/Textures/Books/Products/3_ui.dds",
    "Libs/UI/Textures/Books/Products/4_ui.dds",
    "Libs/UI/Textures/Books/Products/5_ui.dds",
    "Libs/UI/Textures/Books/Products/6_ui.dds",
    "Libs/UI/Textures/Books/Recipes/replaceme_ui.dds",
    "Libs/UI/Textures/Books/Ingredients/saltpeter_ui.dds",
    "Libs/UI/Textures/Books/Ingredients/special_charcoal_ui.dds",
    "Libs/UI/Textures/Books/Ingredients/special_attire_ui.dds",
    "Libs/UI/Textures/Books/Ingredients/honey_ui.dds",
    "Libs/UI/Textures/Books/Unique/roses_book_01_ui.dds",
    "Libs/UI/Textures/Books/Unique/roses_book_02_ui.dds",
    "Libs/UI/Textures/Books/Unique/sigismund_seal_ui.dds",
}


def specs_for_profile(profile: str) -> tuple[AssetSpec, ...]:
    if profile == "full":
        return ASSET_SPECS
    if profile == "safe":
        return tuple(spec for spec in UI_SPECS if spec.target in SAFE_TARGETS)
    raise SystemExit(f"Unsupported visual profile: {profile}")


def clamp(value: float) -> int:
    return max(0, min(255, int(round(value))))


def rgba(rgb: tuple[int, int, int], alpha: int = 255) -> Color:
    return (rgb[0], rgb[1], rgb[2], alpha)


def load_sources(texture_root: Path) -> dict[str, Image.Image]:
    sources: dict[str, Image.Image] = {}
    for path in texture_root.glob("*.png"):
        try:
            sources[path.stem] = Image.open(path).convert("RGBA")
        except OSError:
            continue
    return sources


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    image = image.convert("RGBA")
    ratio = max(size[0] / image.width, size[1] / image.height)
    resized = image.resize((math.ceil(image.width * ratio), math.ceil(image.height * ratio)), Image.Resampling.LANCZOS)
    x = (resized.width - size[0]) // 2
    y = (resized.height - size[1]) // 2
    return resized.crop((x, y, x + size[0], y + size[1]))


def fit_contain(image: Image.Image, size: tuple[int, int], background: Color = (0, 0, 0, 0)) -> Image.Image:
    target = Image.new("RGBA", size, background)
    src = image.convert("RGBA")
    src.thumbnail(size, Image.Resampling.LANCZOS)
    target.alpha_composite(src, ((size[0] - src.width) // 2, (size[1] - src.height) // 2))
    return target


def add_noise(image: Image.Image, strength: int = 20, seed: int = 7) -> Image.Image:
    rng = random.Random(seed)
    noise = Image.new("RGBA", image.size, (0, 0, 0, 0))
    px = noise.load()
    for y in range(image.height):
        for x in range(image.width):
            value = rng.randint(-strength, strength)
            alpha = abs(value)
            color = (255, 255, 255, alpha) if value >= 0 else (0, 0, 0, alpha)
            px[x, y] = color
    return Image.alpha_composite(image.convert("RGBA"), noise)


def gradient(size: tuple[int, int], top: Color, bottom: Color) -> Image.Image:
    w, h = size
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(clamp(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        draw.line([(0, y), (w, y)], fill=color)
    return image


def parchment(size: tuple[int, int], seed: int = 11, dark: bool = False) -> Image.Image:
    base = (44, 37, 29, 255) if dark else (196, 171, 124, 255)
    hi = (71, 58, 44, 255) if dark else (232, 210, 156, 255)
    image = gradient(size, hi, base)
    image = add_noise(image, 18 if dark else 24, seed)
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    for _ in range(70):
        x = random.Random(seed + _ * 5).randint(0, w)
        y = random.Random(seed + _ * 11).randint(0, h)
        r = random.Random(seed + _ * 17).randint(max(8, w // 80), max(12, w // 22))
        draw.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=(70, 45, 24, 12))
    draw.rectangle((8, 8, w - 9, h - 9), outline=(55, 35, 18, 120), width=max(2, w // 200))
    draw.rectangle((24, 24, w - 25, h - 25), outline=(250, 230, 170, 55), width=max(1, w // 360))
    return image


def overlay_source(
    base: Image.Image,
    source: Image.Image | None,
    box: tuple[int, int, int, int],
    opacity: float = 0.35,
    mode: str = "contain",
) -> None:
    if source is None:
        return
    x1, y1, x2, y2 = box
    size = (max(1, x2 - x1), max(1, y2 - y1))
    fitted = fit_cover(source, size) if mode == "cover" else fit_contain(source, size)
    alpha = fitted.getchannel("A").point(lambda p: clamp(p * opacity))
    fitted.putalpha(alpha)
    base.alpha_composite(fitted, (x1, y1))


def draw_roof(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, color: Color, trim: Color) -> None:
    draw.polygon([(x, y + h), (x + w // 2, y), (x + w, y + h), (x + w + w // 14, y + h + h // 5), (x - w // 14, y + h + h // 5)], fill=color)
    draw.line([(x - w // 14, y + h + h // 5), (x + w + w // 14, y + h + h // 5)], fill=trim, width=max(2, w // 90))
    for i in range(1, 8):
        xx = x + i * w // 8
        draw.line([(xx, y + h // 8), (xx - w // 14, y + h + h // 5)], fill=(22, 40, 39, 95), width=max(1, w // 180))


def draw_city_base(size: tuple[int, int], sources: dict[str, Image.Image], variant: str = "day") -> Image.Image:
    w, h = size
    if variant == "night":
        image = gradient(size, (22, 31, 48, 255), (70, 57, 51, 255))
    else:
        image = gradient(size, (135, 163, 168, 255), (214, 178, 117, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    rng = random.Random(38 + len(variant))

    for layer, color in enumerate(((50, 75, 64, 170), (72, 91, 72, 180), (95, 101, 79, 190))):
        base_y = int(h * (0.30 + 0.06 * layer))
        pts = [(0, base_y)]
        for i in range(9):
            pts.append((i * w // 8, base_y - rng.randint(h // 20, h // 8)))
        pts.extend([(w, h), (0, h)])
        draw.polygon(pts, fill=color)

    wall_y = int(h * 0.58)
    draw.rectangle((0, wall_y, w, h), fill=(108, 104, 88, 255))
    for y in range(wall_y + h // 45, h, h // 16):
        draw.line((0, y, w, y + rng.randint(-4, 4)), fill=(55, 55, 50, 95), width=max(2, h // 220))
    for x in range(-w // 10, w, w // 7):
        draw.line((x, wall_y, x + w // 12, h), fill=(61, 60, 54, 80), width=max(1, w // 260))

    gate_x = w // 2 - w // 7
    gate_w = w // 3
    gate_h = h // 3
    draw.rectangle((gate_x, wall_y - gate_h // 3, gate_x + gate_w, wall_y + gate_h), fill=(86, 60, 39, 255))
    overlay_source(image, sources.get("Kr_House_Door_01_D"), (gate_x + gate_w // 8, wall_y, gate_x + gate_w * 7 // 8, wall_y + gate_h), 0.55, "cover")
    draw.rectangle((gate_x, wall_y - gate_h // 3, gate_x + gate_w, wall_y + gate_h), outline=(36, 28, 21, 170), width=max(3, w // 170))
    draw_roof(draw, gate_x - gate_w // 7, wall_y - gate_h // 2, gate_w + gate_w // 3, h // 8, (35, 67, 62, 245), (15, 27, 24, 220))

    for i, x in enumerate((w // 9, w // 4, w * 3 // 4, w * 8 // 9)):
        y = wall_y - rng.randint(h // 14, h // 9)
        house_w = rng.randint(w // 7, w // 5)
        house_h = rng.randint(h // 8, h // 5)
        draw.rectangle((x - house_w // 2, y, x + house_w // 2, y + house_h), fill=(196, 183, 148, 240))
        draw.rectangle((x - house_w // 2, y, x + house_w // 2, y + house_h), outline=(70, 50, 35, 110), width=max(1, w // 360))
        draw_roof(draw, x - house_w // 2 - house_w // 10, y - house_h // 3, house_w + house_w // 5, house_h // 3, (43, 74, 65, 235), (18, 29, 26, 210))
        for bx in range(x - house_w // 2 + house_w // 5, x + house_w // 2, house_w // 4):
            draw.rectangle((bx, y + house_h // 4, bx + max(3, house_w // 25), y + house_h), fill=(68, 44, 25, 130))

    beacon_x = int(w * 0.78)
    beacon_y = int(h * 0.36)
    draw.line((beacon_x, beacon_y + h // 10, beacon_x - w // 35, wall_y), fill=(64, 40, 25, 220), width=max(4, w // 120))
    draw.line((beacon_x, beacon_y + h // 10, beacon_x + w // 35, wall_y), fill=(64, 40, 25, 220), width=max(4, w // 120))
    overlay_source(image, sources.get("fx_fire_59a"), (beacon_x - w // 16, beacon_y - h // 16, beacon_x + w // 16, beacon_y + h // 14), 0.75)
    overlay_source(image, sources.get("fx_smoke_04a") or sources.get("FX_Smoke_19a"), (beacon_x - w // 12, beacon_y - h // 5, beacon_x + w // 8, beacon_y + h // 18), 0.35)

    if variant in {"alley", "market"}:
        draw.rectangle((0, int(h * 0.72), w, h), fill=(84, 69, 52, 180))
        for x in range(-w // 4, w + w // 4, w // 6):
            draw.polygon([(x, h), (x + w // 15, int(h * 0.67)), (x + w // 7, h)], fill=(48, 38, 30, 90))
        if variant == "market":
            for x in range(w // 8, w, w // 5):
                draw.ellipse((x, int(h * 0.70), x + w // 18, int(h * 0.76)), fill=(125, 75, 49, 230))
                draw.rectangle((x - w // 45, int(h * 0.76), x + w // 15, int(h * 0.84)), fill=(78, 45, 26, 220))

    if variant == "night":
        image = ImageEnhance.Brightness(image).enhance(0.78)
        moon = Image.new("RGBA", size, (0, 0, 0, 0))
        md = ImageDraw.Draw(moon, "RGBA")
        md.ellipse((w // 9, h // 11, w // 9 + w // 13, h // 11 + w // 13), fill=(224, 210, 170, 150))
        image = Image.alpha_composite(image, moon.filter(ImageFilter.GaussianBlur(max(1, w // 220))))

    image = add_noise(image, 9, 42)
    return image


def make_map(size: tuple[int, int], sources: dict[str, Image.Image], variant: str = "routes") -> Image.Image:
    image = parchment(size, 91)
    w, h = size
    draw = ImageDraw.Draw(image, "RGBA")
    overlay_source(image, sources.get("WaterColor_FieldOcean"), (0, 0, w, h), 0.16, "cover")
    coast = [(int(w * 0.18), int(h * 0.05)), (int(w * 0.11), int(h * 0.20)), (int(w * 0.17), int(h * 0.38)), (int(w * 0.12), int(h * 0.56)), (int(w * 0.25), int(h * 0.84)), (int(w * 0.20), h)]
    draw.line(coast, fill=(61, 79, 73, 170), width=max(3, w // 160), joint="curve")
    draw.polygon([(0, 0), *coast, (0, h)], fill=(64, 101, 111, 42))
    roads = [
        [(int(w * 0.23), int(h * 0.76)), (int(w * 0.38), int(h * 0.62)), (int(w * 0.52), int(h * 0.53)), (int(w * 0.77), int(h * 0.38))],
        [(int(w * 0.35), int(h * 0.62)), (int(w * 0.46), int(h * 0.74)), (int(w * 0.64), int(h * 0.81))],
        [(int(w * 0.46), int(h * 0.54)), (int(w * 0.57), int(h * 0.35)), (int(w * 0.70), int(h * 0.23))],
    ]
    for road in roads:
        draw.line(road, fill=(100, 56, 38, 190), width=max(4, w // 125), joint="curve")
        draw.line(road, fill=(229, 193, 128, 95), width=max(1, w // 360), joint="curve")
    for x, y, kind in (
        (0.25, 0.76, "port"),
        (0.39, 0.62, "gate"),
        (0.53, 0.53, "camp"),
        (0.78, 0.38, "beacon"),
        (0.66, 0.80, "store"),
    ):
        cx, cy = int(w * x), int(h * y)
        draw.ellipse((cx - w // 42, cy - w // 42, cx + w // 42, cy + w // 42), fill=(104, 39, 31, 220))
        draw.ellipse((cx - w // 70, cy - w // 70, cx + w // 70, cy + w // 70), fill=(240, 211, 151, 230))
        if kind == "beacon":
            draw.polygon([(cx, cy - w // 20), (cx - w // 28, cy + w // 22), (cx + w // 28, cy + w // 22)], outline=(70, 40, 22, 210), fill=(204, 103, 46, 100))
    for i in range(8):
        mx = int(w * (0.43 + 0.06 * (i % 4)))
        my = int(h * (0.18 + 0.06 * (i // 2)))
        draw.polygon([(mx, my - h // 22), (mx - w // 45, my + h // 40), (mx + w // 45, my + h // 40)], fill=(80, 82, 61, 95), outline=(62, 58, 44, 120))
    if variant == "fort":
        draw.rectangle((int(w * 0.33), int(h * 0.31), int(w * 0.62), int(h * 0.47)), outline=(70, 40, 22, 220), width=max(4, w // 140))
        draw.rectangle((int(w * 0.42), int(h * 0.36), int(w * 0.53), int(h * 0.47)), fill=(70, 40, 22, 90))
    return image.filter(ImageFilter.UnsharpMask(radius=1.4, percent=90, threshold=3))


def make_panel(size: tuple[int, int], sources: dict[str, Image.Image], dark: bool = False) -> Image.Image:
    image = parchment(size, 33, dark=dark)
    w, h = size
    draw = ImageDraw.Draw(image, "RGBA")
    overlay_source(image, sources.get("Atlas_IMJIN_Window_32bit"), (0, 0, w, h), 0.22, "cover")
    draw.rectangle((w // 18, h // 18, w - w // 18, h - h // 18), outline=(45, 28, 17, 150), width=max(3, w // 160))
    for y in (h // 7, h * 6 // 7):
        draw.line((w // 10, y, w * 9 // 10, y), fill=(122, 69, 35, 130), width=max(2, h // 180))
    for x in range(w // 8, w * 7 // 8, max(20, w // 13)):
        draw.ellipse((x - w // 90, h // 11 - w // 90, x + w // 90, h // 11 + w // 90), fill=(132, 37, 30, 120))
    return image


def icon_background(size: tuple[int, int], color: Color = (58, 42, 30, 255)) -> Image.Image:
    image = gradient(size, (min(color[0] + 30, 255), min(color[1] + 22, 255), min(color[2] + 15, 255), 255), color)
    image = add_noise(image, 12, 55)
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    pad = max(8, w // 18)
    draw.rounded_rectangle((pad, pad, w - pad, h - pad), radius=max(8, w // 18), outline=(226, 190, 126, 160), width=max(3, w // 80), fill=(20, 16, 12, 52))
    draw.ellipse((pad * 2, pad * 2, w - pad * 2, h - pad * 2), outline=(32, 24, 18, 100), width=max(2, w // 120))
    return image


def draw_sword(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.polygon([(w * 51 // 100, h * 12 // 100), (w * 58 // 100, h * 16 // 100), (w * 42 // 100, h * 70 // 100), (w * 35 // 100, h * 66 // 100)], fill=(188, 191, 181, 255), outline=(44, 45, 43, 160))
    draw.line((w * 51 // 100, h * 15 // 100, w * 40 // 100, h * 68 // 100), fill=(244, 238, 213, 160), width=max(2, w // 70))
    draw.rectangle((w * 30 // 100, h * 66 // 100, w * 58 // 100, h * 72 // 100), fill=(43, 66, 58, 255), outline=(18, 28, 24, 200))
    draw.rectangle((w * 39 // 100, h * 70 // 100, w * 46 // 100, h * 90 // 100), fill=(86, 46, 25, 255), outline=(36, 20, 12, 200))
    draw.ellipse((w * 37 // 100, h * 87 // 100, w * 48 // 100, h * 96 // 100), fill=(128, 35, 31, 255), outline=(42, 15, 12, 160))


def draw_bow(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.arc((w * 20 // 100, h * 12 // 100, w * 85 // 100, h * 92 // 100), 105, 260, fill=(96, 52, 28, 255), width=max(5, w // 32))
    draw.arc((w * 24 // 100, h * 15 // 100, w * 83 // 100, h * 88 // 100), 105, 260, fill=(216, 171, 100, 150), width=max(2, w // 100))
    draw.line((w * 43 // 100, h * 16 // 100, w * 43 // 100, h * 88 // 100), fill=(220, 213, 182, 220), width=max(1, w // 160))
    for offset in (0, w // 20):
        draw.line((w * 28 // 100 + offset, h * 68 // 100, w * 78 // 100 + offset, h * 33 // 100), fill=(188, 188, 172, 255), width=max(2, w // 90))
        draw.polygon([(w * 78 // 100 + offset, h * 33 // 100), (w * 72 // 100 + offset, h * 34 // 100), (w * 75 // 100 + offset, h * 39 // 100)], fill=(48, 69, 62, 255))


def draw_shield(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    pts = [(w // 2, h * 12 // 100), (w * 78 // 100, h * 24 // 100), (w * 72 // 100, h * 68 // 100), (w // 2, h * 88 // 100), (w * 28 // 100, h * 68 // 100), (w * 22 // 100, h * 24 // 100)]
    draw.polygon(pts, fill=(43, 83, 74, 255), outline=(18, 28, 24, 220))
    draw.polygon([(w // 2, h * 17 // 100), (w * 68 // 100, h * 27 // 100), (w * 63 // 100, h * 63 // 100), (w // 2, h * 78 // 100)], fill=(126, 38, 32, 205))
    draw.line((w // 2, h * 16 // 100, w // 2, h * 80 // 100), fill=(228, 198, 126, 190), width=max(3, w // 50))
    draw.ellipse((w * 42 // 100, h * 40 // 100, w * 58 // 100, h * 56 // 100), fill=(224, 184, 98, 230), outline=(38, 25, 16, 190))


def draw_scroll(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.rounded_rectangle((w * 22 // 100, h * 18 // 100, w * 78 // 100, h * 80 // 100), radius=w // 25, fill=(226, 202, 148, 255), outline=(93, 55, 31, 170), width=max(2, w // 90))
    for i in range(5):
        y = h * (28 + i * 9) // 100
        draw.line((w * 31 // 100, y, w * 68 // 100, y), fill=(84, 54, 34, 135), width=max(1, w // 150))
    draw.ellipse((w * 55 // 100, h * 57 // 100, w * 73 // 100, h * 75 // 100), fill=(137, 36, 31, 230), outline=(65, 18, 15, 180))
    draw.line((w * 63 // 100, h * 61 // 100, w * 65 // 100, h * 71 // 100), fill=(236, 191, 107, 180), width=max(1, w // 120))


def draw_ration(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.ellipse((w * 26 // 100, h * 40 // 100, w * 76 // 100, h * 84 // 100), fill=(114, 73, 40, 255), outline=(52, 32, 18, 200), width=max(3, w // 70))
    draw.rectangle((w * 32 // 100, h * 28 // 100, w * 70 // 100, h * 67 // 100), fill=(177, 144, 86, 255), outline=(61, 39, 22, 180), width=max(2, w // 90))
    draw.arc((w * 34 // 100, h * 17 // 100, w * 69 // 100, h * 42 // 100), 200, 340, fill=(48, 74, 64, 230), width=max(4, w // 50))
    for i in range(7):
        x = w * (36 + i * 5) // 100
        draw.line((x, h * 35 // 100, x + w // 24, h * 58 // 100), fill=(92, 57, 31, 90), width=max(1, w // 130))


def draw_powder(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.rectangle((w * 35 // 100, h * 20 // 100, w * 67 // 100, h * 76 // 100), fill=(64, 48, 38, 255), outline=(29, 22, 18, 220), width=max(3, w // 70))
    draw.rectangle((w * 39 // 100, h * 12 // 100, w * 63 // 100, h * 24 // 100), fill=(123, 81, 43, 255), outline=(41, 26, 16, 220))
    draw.ellipse((w * 28 // 100, h * 68 // 100, w * 78 // 100, h * 90 // 100), fill=(33, 29, 26, 210))
    for i in range(14):
        x = w * (28 + (i * 7) % 45) // 100
        y = h * (68 + (i * 5) % 19) // 100
        draw.ellipse((x, y, x + w // 45, y + w // 45), fill=(18, 18, 17, 220))


def draw_armor(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.polygon([(w * 32 // 100, h * 20 // 100), (w * 68 // 100, h * 20 // 100), (w * 77 // 100, h * 82 // 100), (w * 23 // 100, h * 82 // 100)], fill=(52, 84, 73, 255), outline=(19, 31, 27, 220))
    draw.polygon([(w * 42 // 100, h * 22 // 100), (w * 58 // 100, h * 22 // 100), (w * 53 // 100, h * 44 // 100), (w * 47 // 100, h * 44 // 100)], fill=(202, 184, 139, 240))
    for y in range(h * 48 // 100, h * 77 // 100, max(5, h // 12)):
        draw.line((w * 30 // 100, y, w * 70 // 100, y), fill=(218, 187, 109, 170), width=max(2, w // 80))
    draw.rectangle((w * 27 // 100, h * 33 // 100, w * 73 // 100, h * 40 // 100), fill=(112, 37, 31, 210))


def draw_medicine(draw: ImageDraw.ImageDraw, w: int, h: int) -> None:
    draw.rounded_rectangle((w * 33 // 100, h * 21 // 100, w * 67 // 100, h * 82 // 100), radius=w // 18, fill=(209, 194, 149, 255), outline=(63, 44, 27, 190), width=max(3, w // 80))
    draw.rectangle((w * 39 // 100, h * 11 // 100, w * 61 // 100, h * 25 // 100), fill=(83, 50, 31, 255), outline=(42, 24, 15, 180))
    draw.line((w // 2, h * 39 // 100, w // 2, h * 66 // 100), fill=(129, 42, 35, 230), width=max(4, w // 42))
    draw.line((w * 38 // 100, h * 52 // 100, w * 62 // 100, h * 52 // 100), fill=(129, 42, 35, 230), width=max(4, w // 42))


def make_icon(size: tuple[int, int], sources: dict[str, Image.Image], kind: str) -> Image.Image:
    palette = {
        "sword": (56, 43, 31, 255),
        "bow": (51, 61, 45, 255),
        "shield": (41, 58, 56, 255),
        "dispatch": (70, 50, 37, 255),
        "ration": (83, 58, 36, 255),
        "beacon": (62, 42, 34, 255),
        "powder": (45, 43, 39, 255),
        "charcoal": (39, 39, 35, 255),
        "armor": (42, 62, 57, 255),
        "medicine": (67, 55, 41, 255),
    }
    image = icon_background(size, palette.get(kind, (58, 42, 30, 255)))
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    if kind == "sword" and sources.get("KR_S_Sword_00_D") is not None:
        overlay_source(image, sources["KR_S_Sword_00_D"], (w // 8, h // 8, w * 7 // 8, h * 7 // 8), 0.95)
        draw_sword(draw, w, h)
    elif kind == "sword":
        draw_sword(draw, w, h)
    elif kind == "bow":
        draw_bow(draw, w, h)
    elif kind == "shield":
        draw_shield(draw, w, h)
    elif kind == "dispatch":
        draw_scroll(draw, w, h)
    elif kind == "ration":
        draw_ration(draw, w, h)
    elif kind == "beacon":
        overlay_source(image, sources.get("fx_fire_59a"), (w // 5, h // 7, w * 4 // 5, h * 4 // 5), 0.78)
        draw.line((w * 32 // 100, h * 82 // 100, w // 2, h * 50 // 100), fill=(64, 39, 24, 220), width=max(5, w // 38))
        draw.line((w * 68 // 100, h * 82 // 100, w // 2, h * 50 // 100), fill=(64, 39, 24, 220), width=max(5, w // 38))
    elif kind == "powder":
        draw_powder(draw, w, h)
    elif kind == "charcoal":
        draw_powder(draw, w, h)
        draw.rectangle((w * 27 // 100, h * 70 // 100, w * 78 // 100, h * 84 // 100), fill=(22, 22, 20, 230))
    elif kind == "armor":
        draw_armor(draw, w, h)
    elif kind == "medicine":
        draw_medicine(draw, w, h)
    else:
        draw_scroll(draw, w, h)
    return image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=100, threshold=2))


def make_icon_sheet(size: tuple[int, int], sources: dict[str, Image.Image], small: bool = False) -> Image.Image:
    image = parchment(size, 64, dark=True)
    w, h = size
    kinds = ["sword", "bow", "shield", "dispatch", "ration", "beacon", "powder", "armor"] if not small else ["sword", "bow", "shield", "dispatch"]
    cols = 4
    rows = math.ceil(len(kinds) / cols)
    cell_w = w // cols
    cell_h = h // rows
    for idx, kind in enumerate(kinds):
        cell = make_icon((min(cell_w, cell_h) - max(12, w // 60), min(cell_w, cell_h) - max(12, w // 60)), sources, kind)
        x = (idx % cols) * cell_w + (cell_w - cell.width) // 2
        y = (idx // cols) * cell_h + (cell_h - cell.height) // 2
        image.alpha_composite(cell, (x, y))
    return image


def make_shield_strip(size: tuple[int, int], sources: dict[str, Image.Image]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = size
    for i, kind in enumerate(("shield", "armor")):
        icon = make_icon((h, h), sources, kind)
        image.alpha_composite(icon, (i * h, 0))
    return image


def make_buff_disks(size: tuple[int, int], sources: dict[str, Image.Image]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = size
    for idx, kind in enumerate(("beacon", "powder", "medicine", "shield")):
        cell = make_icon((w // 2, h // 2), sources, kind)
        image.alpha_composite(cell, ((idx % 2) * w // 2, (idx // 2) * h // 2))
    return image


def make_seal(size: tuple[int, int], sources: dict[str, Image.Image]) -> Image.Image:
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image, "RGBA")
    w, h = size
    draw.ellipse((w // 8, h // 8, w * 7 // 8, h * 7 // 8), fill=(147, 35, 31, 235), outline=(73, 17, 16, 220), width=max(4, w // 32))
    draw.rectangle((w * 34 // 100, h * 25 // 100, w * 66 // 100, h * 75 // 100), outline=(235, 172, 94, 190), width=max(3, w // 48))
    draw.line((w * 25 // 100, h // 2, w * 75 // 100, h // 2), fill=(235, 172, 94, 180), width=max(3, w // 56))
    draw.line((w // 2, h * 25 // 100, w // 2, h * 75 // 100), fill=(235, 172, 94, 180), width=max(3, w // 56))
    return image.filter(ImageFilter.GaussianBlur(0.2))


def make_recipe_page(size: tuple[int, int], sources: dict[str, Image.Image]) -> Image.Image:
    image = parchment(size, 106)
    w, h = size
    draw = ImageDraw.Draw(image, "RGBA")
    overlay_source(image, sources.get("Kr_House_Door_01_D"), (w * 58 // 100, h * 14 // 100, w * 90 // 100, h * 47 // 100), 0.26, "cover")
    for i in range(12):
        y = h * (18 + i * 5) // 100
        draw.line((w * 12 // 100, y, w * 52 // 100, y), fill=(79, 49, 30, 105), width=max(1, w // 350))
    icon = make_icon((w // 4, w // 4), sources, "powder")
    image.alpha_composite(icon, (w * 60 // 100, h * 58 // 100))
    draw_scroll(draw, w // 2, h // 2)
    return image


def make_material(size: tuple[int, int], sources: dict[str, Image.Image], kind: str) -> Image.Image:
    w, h = size
    if "stone" in kind:
        image = Image.new("RGBA", size, (96, 94, 82, 255))
        draw = ImageDraw.Draw(image, "RGBA")
        rng = random.Random(120)
        y = 0
        while y < h:
            row_h = rng.randint(h // 12, h // 7)
            x = -rng.randint(0, w // 7)
            while x < w:
                cell_w = rng.randint(w // 8, w // 4)
                shade = rng.randint(-22, 22)
                color = (clamp(99 + shade), clamp(96 + shade), clamp(82 + shade), 255)
                draw.rectangle((x, y, x + cell_w, y + row_h), fill=color, outline=(50, 49, 45, 150), width=max(1, w // 360))
                x += cell_w
            y += row_h
        if "moss" in kind:
            for _ in range(90):
                x = rng.randint(0, w)
                y = rng.randint(0, h)
                draw.ellipse((x, y, x + rng.randint(10, 45), y + rng.randint(6, 28)), fill=(53, 78, 55, 55))
        return add_noise(image, 10, 121)
    if "window" in kind:
        image = parchment(size, 122)
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rectangle((0, 0, w, h), fill=(220, 209, 169, 235))
        for x in range(0, w + 1, w // 5):
            draw.line((x, 0, x, h), fill=(63, 42, 27, 230), width=max(5, w // 80))
        for y in range(0, h + 1, h // 5):
            draw.line((0, y, w, y), fill=(63, 42, 27, 230), width=max(5, h // 80))
        for i in range(-h, w, w // 5):
            draw.line((i, 0, i + h, h), fill=(90, 61, 39, 90), width=max(2, w // 140))
        return add_noise(image, 8, 124)
    if "wood" in kind or ("beams" in kind and "plaster" not in kind):
        image = Image.new("RGBA", size, (82, 48, 28, 255))
        draw = ImageDraw.Draw(image, "RGBA")
        rng = random.Random(125)
        orientation = "vertical" if "beams" in kind else "horizontal"
        count = 8 if orientation == "horizontal" else 6
        for i in range(count):
            if orientation == "horizontal":
                y1 = i * h // count
                y2 = (i + 1) * h // count
                color = (clamp(80 + rng.randint(-20, 18)), clamp(48 + rng.randint(-12, 14)), clamp(28 + rng.randint(-10, 12)), 255)
                draw.rectangle((0, y1, w, y2), fill=color)
                draw.line((0, y2, w, y2), fill=(28, 18, 12, 170), width=max(2, h // 180))
                for _ in range(5):
                    yy = rng.randint(y1, max(y1, y2 - 1))
                    draw.line((0, yy, w, yy + rng.randint(-7, 7)), fill=(150, 99, 54, 38), width=max(1, h // 320))
            else:
                x1 = i * w // count
                x2 = (i + 1) * w // count
                draw.rectangle((x1, 0, x2, h), fill=(69 + rng.randint(-10, 18), 43 + rng.randint(-8, 11), 24 + rng.randint(-5, 9), 255))
                draw.line((x2, 0, x2, h), fill=(29, 18, 12, 170), width=max(2, w // 170))
        overlay_source(image, sources.get("Kr_House_Door_01_D"), (0, 0, w, h), 0.20, "cover")
        return add_noise(image, 9, 126)
    image = parchment(size, 127)
    draw = ImageDraw.Draw(image, "RGBA")
    if "beams" in kind:
        draw.rectangle((0, 0, w, h), fill=(206, 193, 154, 255))
    for x in range(0, w, w // 4):
        draw.rectangle((x, 0, x + max(8, w // 24), h), fill=(79, 49, 28, 200))
    for y in range(0, h, h // 4):
        draw.rectangle((0, y, w, y + max(8, h // 28)), fill=(78, 47, 27, 170))
    if "cracked" in kind:
        for i in range(18):
            x = (i * 57) % w
            y = (i * 91) % h
            draw.line((x, y, x + w // 9, y + h // 13), fill=(85, 69, 49, 80), width=max(1, w // 300))
    return add_noise(image, 12, 128)


def generate_image(spec: AssetSpec, sources: dict[str, Image.Image]) -> Image.Image:
    gen = spec.generator
    if gen == "city_gate":
        return draw_city_base(spec.size, sources, "day")
    if gen == "city_gate_night":
        return draw_city_base(spec.size, sources, "night")
    if gen == "city_alley":
        return draw_city_base(spec.size, sources, "alley")
    if gen == "city_market":
        return draw_city_base(spec.size, sources, "market")
    if gen in {"fort_beacon", "city_wall"}:
        return draw_city_base(spec.size, sources, "day")
    if gen in {"map", "map_routes"}:
        return make_map(spec.size, sources, "routes")
    if gen == "map_fort":
        return make_map(spec.size, sources, "fort")
    if gen == "panel":
        return make_panel(spec.size, sources, False)
    if gen in {"panel_dark", "item_info"}:
        return make_panel(spec.size, sources, True)
    if gen == "panel_inventory":
        return make_panel(spec.size, sources, False)
    if gen == "paper_list":
        return parchment(spec.size, 44)
    if gen == "ornament":
        image = Image.new("RGBA", spec.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        w, h = spec.size
        draw.line((w // 10, h // 2, w * 9 // 10, h // 2), fill=(183, 137, 77, 180), width=max(4, h // 9))
        for x in (w // 8, w * 7 // 8):
            draw.ellipse((x - h // 4, h // 4, x + h // 4, h * 3 // 4), outline=(126, 39, 31, 180), width=max(3, h // 14))
        return image
    if gen == "icon_sheet":
        return make_icon_sheet(spec.size, sources, False)
    if gen == "small_icon_sheet":
        return make_icon_sheet(spec.size, sources, True)
    if gen == "shield_strip":
        return make_shield_strip(spec.size, sources)
    if gen == "buff_disks":
        return make_buff_disks(spec.size, sources)
    if gen == "character_slot":
        image = make_icon(spec.size, sources, "armor")
        overlay_source(image, sources.get("Logo_TitleScreen"), (0, 0, spec.size[0], spec.size[1]), 0.18, "contain")
        return image
    if gen == "seal":
        return make_seal(spec.size, sources)
    if gen == "attack_mode":
        image = make_panel(spec.size, sources, True)
        icon = make_icon((spec.size[1], spec.size[1]), sources, "sword")
        image.alpha_composite(icon, (spec.size[0] // 2 - icon.width // 2, 0))
        return image
    if gen == "recipe_page":
        return make_recipe_page(spec.size, sources)
    if gen == "seal_document":
        image = make_recipe_page(spec.size, sources)
        seal = make_seal((spec.size[0] // 3, spec.size[0] // 3), sources)
        image.alpha_composite(seal, (spec.size[0] * 58 // 100, spec.size[1] * 58 // 100))
        return image
    if gen.startswith("icon_"):
        return make_icon(spec.size, sources, gen.removeprefix("icon_"))
    if gen in {"hanok_plaster", "hanok_plaster_beams", "hanok_plaster_cracked", "joseon_stone", "joseon_stone_moss", "joseon_gate_wood", "joseon_gate_wood_dark", "joseon_beams", "hanji_window"}:
        return make_material(spec.size, sources, gen)
    return parchment(spec.size)


def save_dds(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGBA").save(path, format="DDS")


def force_opaque(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    image.putalpha(255)
    return image


def package_stage(stage_root: Path, pak_path: Path) -> int:
    if pak_path.exists():
        pak_path.unlink()
    pak_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(pak_path, "w", compression=zipfile.ZIP_STORED) as archive:
        for file_path in sorted(stage_root.rglob("*")):
            if not file_path.is_file():
                continue
            archive.write(file_path, file_path.relative_to(stage_root).as_posix())
            count += 1
    return count


def build_visual_pack(private_root: Path, kcd2_mod_root: Path, output_root: Path, profile: str) -> dict:
    texture_root = private_root / "textures"
    if not texture_root.exists():
        raise SystemExit(f"Extracted ImjinWar texture folder was not found: {texture_root}")

    stage_root = output_root / "kcd2_visual_pack_stage"
    preview_root = output_root / "previews"
    if stage_root.exists():
        shutil.rmtree(stage_root)
    if preview_root.exists():
        shutil.rmtree(preview_root)
    stage_root.mkdir(parents=True, exist_ok=True)
    preview_root.mkdir(parents=True, exist_ok=True)

    sources = load_sources(texture_root)
    selected_specs = specs_for_profile(profile)
    entries: list[dict] = []
    for spec in selected_specs:
        image = generate_image(spec, sources)
        if spec.target.startswith("Textures/structures/") or spec.generator not in TRANSPARENT_GENERATORS:
            image = force_opaque(image)
        dds_path = stage_root / spec.target
        png_path = preview_root / f"{spec.label}.png"
        save_dds(image, dds_path)
        png_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(png_path)
        entries.append(
            {
                "target": spec.target,
                "size": list(spec.size),
                "generator": spec.generator,
                "label": spec.label,
                "preview": str(png_path),
            }
        )

    pak_path = kcd2_mod_root / "Data" / "joseon_counterattack_private_ui.pak"
    package_count = package_stage(stage_root, pak_path)
    manifest = {
        "status": "ok",
        "private_root": str(private_root),
        "output_root": str(output_root),
        "pak_path": str(pak_path),
        "entry_count": package_count,
        "profile": profile,
        "source_texture_count": len(sources),
        "ui_entry_count": len([spec for spec in selected_specs if not spec.target.startswith("Textures/structures/")]),
        "city_texture_entry_count": len([spec for spec in selected_specs if spec.target.startswith("Textures/structures/")]),
        "entries": entries,
        "note": "Local-only visual pack. It contains generated assets plus local ImjinWar-derived composites and must not be redistributed.",
    }
    (output_root / "visual_asset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--kcd2-mod-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--profile", choices=("safe", "full"), default="safe")
    args = parser.parse_args()

    result = build_visual_pack(Path(args.private_root), Path(args.kcd2_mod_root), Path(args.output), args.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
