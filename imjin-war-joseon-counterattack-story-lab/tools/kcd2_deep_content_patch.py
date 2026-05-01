#!/usr/bin/env python
"""Deep content patcher for the local KCD2 Joseon Counterattack mod.

The base PowerShell build creates a working mod shell. This patcher adds a more
immersive layer: codex rewrites, richer item/character text, and a starter
inventory that makes the player begin with a Joseon land-front kit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET
import zipfile


LOCALIZATION_ENTRIES = ("text_ui_menus.xml", "text_ui_items.xml", "text_ui_soul.xml")


KO_CODEX = [
    (
        "1592년 임진왜란 초전",
        "<years>1592년 4월</years><paragraph>부산포와 부산진에서 시작된 전쟁의 첫 충격은 조선의 방어 체계를 순식간에 흔들었습니다. 이 팬픽 모드는 거대한 승리보다 먼저 장계, 봉수, 성문, 식량, 피난민을 붙드는 초반 며칠에 초점을 둡니다.</paragraph><paragraph>플레이어는 바다에서 직접 싸우지 않습니다. 이순신 장군은 살아 있으며 남해 수군을 준비하고, 플레이어는 육지에서 그 시간이 무너지지 않도록 지켜야 합니다.</paragraph>",
    ),
    (
        "부산진과 동래성",
        "<paragraph>부산진과 동래성은 조선 남부 방어선이 처음 시험받은 관문입니다. 여기서 하루를 버티면 전령 하나가 살아나고, 전령 하나가 살아나면 수군과 조정이 움직일 시간이 생깁니다.</paragraph><paragraph>성은 돌담만으로 버티지 않습니다. 창고 열쇠, 물길, 활시위, 성문 앞의 질서가 함께 버텨야 합니다.</paragraph>",
    ),
    (
        "이순신 생존 원칙",
        "<paragraph>이 세계관에서 이순신 장군은 죽지 않습니다. 그는 바다에서 반격의 시간을 만들고, 플레이어는 육지에서 그 시간이 끊기지 않도록 장계와 보급로를 지킵니다.</paragraph><paragraph>따라서 이순신은 단순한 배경 인물이 아니라 모든 방어전의 희망 축입니다. 그의 이름이 전해지는 것만으로도 무너진 전열이 다시 서게 됩니다.</paragraph>",
    ),
    (
        "장계와 봉수",
        "<paragraph>전쟁 초기의 가장 강한 무기는 때로 칼이 아니라 글입니다. 봉인이 살아 있는 장계는 어느 성이 버틸지, 어느 길이 막힐지, 어느 수군영이 먼저 움직일지를 가릅니다.</paragraph><paragraph>봉수는 밤하늘의 언어입니다. 불빛 하나가 꺼지면 한 마을이 고립되고, 불빛 하나가 살아나면 세 군영이 동시에 깨어납니다.</paragraph>",
    ),
    (
        "조총과 지상전",
        "<paragraph>처음 듣는 조총 소리는 병사들의 마음을 먼저 무너뜨립니다. 이 모드의 지상전은 그 공포를 이해하고, 사격 간격을 읽고, 좁은 길과 성문에서 다시 붙는 전투를 중심으로 합니다.</paragraph><paragraph>해상전의 영웅담을 그대로 옮기기보다, KCD2의 검, 활, 방어, 기력 관리가 살아 있는 육상 방어전으로 재해석합니다.</paragraph>",
    ),
    (
        "관군과 의병",
        "<paragraph>명령 체계가 무너진 전쟁 초반에는 관군과 의병이 서로를 의심합니다. 그러나 같은 봉화 신호, 같은 퇴각 지점, 같은 군량 장부가 만들어지면 흩어진 사람들이 다시 전선이 됩니다.</paragraph><paragraph>플레이어의 설득과 전달, 물자 배분은 전투만큼 중요합니다.</paragraph>",
    ),
    (
        "전시 보급",
        "<paragraph>곡식, 소금, 말먹이, 붕대, 화살, 방습 주머니는 모두 전장의 생명줄입니다. 전시 보급은 단순한 부가 목표가 아니라, 내일의 전투가 가능한지 결정하는 중심 임무입니다.</paragraph><paragraph>이 모드의 아이템은 조선 초기전의 물자와 장계, 방어 준비를 느끼도록 이름과 설명이 다시 구성됩니다.</paragraph>",
    ),
    (
        "조선의 반격",
        "<paragraph>반격은 대승의 순간에서 시작되지 않습니다. 부상자를 데려오고, 젖은 화약을 말리고, 식량 장부를 다시 쓰고, 거짓 장계를 가려내는 작은 행동이 쌓일 때 반격은 작전이 됩니다.</paragraph><paragraph>동래성의 새벽은 패배를 지우는 이야기가 아니라, 패배 속에서도 무너지지 않는 질서를 다시 세우는 이야기입니다.</paragraph>",
    ),
]

EN_CODEX = [
    (
        "The Opening of the Imjin War",
        "<years>April 1592</years><paragraph>The first shock at Busanjin and Dongnae tore through Joseon's southern defenses. This fan mod focuses on the first days: dispatches, beacons, gates, grain, refugees, and the fragile order that must survive before any great victory is possible.</paragraph><paragraph>The player does not command a naval battle. Admiral Yi Sun-sin lives and prepares the southern fleet while the land road is held long enough for that preparation to matter.</paragraph>",
    ),
    (
        "Busanjin and Dongnae",
        "<paragraph>Busanjin and Dongnae are the first gates of the southern front. Holding one more day can save a courier; saving a courier can wake a naval camp or a court office in time.</paragraph><paragraph>A fortress is not held by stone alone. Keys, wells, bowstrings, ledgers, and order at the gate all have to hold with it.</paragraph>",
    ),
    (
        "Yi Sun-sin Lives",
        "<paragraph>In this storyline Admiral Yi Sun-sin does not die. He creates time at sea; the player protects that time on land by keeping dispatches and supply roads alive.</paragraph><paragraph>His name is not decorative lore. News that Yi still stands is a strategic and moral force that can stiffen a collapsing line.</paragraph>",
    ),
    (
        "Dispatches and Beacons",
        "<paragraph>In the first days of war, the strongest weapon may be a sealed sheet of paper. A living dispatch decides which fortress holds, which road closes, and which naval camp moves first.</paragraph><paragraph>Beacons are the language of the night. If one light dies, a village is isolated. If one light survives, three camps may wake together.</paragraph>",
    ),
    (
        "Arquebuses and Land Combat",
        "<paragraph>The first sound of arquebuses breaks morale before it breaks armor. This mod turns that fear into land combat: reading the firing rhythm, crossing the gap, and holding narrow roads and gates.</paragraph><paragraph>Instead of copying a naval legend onto a land game, it uses KCD2's swordplay, archery, blocking, and stamina as an early Joseon defense story.</paragraph>",
    ),
    (
        "Regulars and Righteous Armies",
        "<paragraph>When command breaks, regular troops and local militias do not automatically trust one another. Shared beacon signals, fallback points, and supply rules turn scattered people into a front.</paragraph><paragraph>Persuasion, delivery, and distribution matter as much as the fight itself.</paragraph>",
    ),
    (
        "Wartime Supply",
        "<paragraph>Grain, salt, fodder, bandages, arrows, and oiled powder bags are the lifelines of the front. Supply is not side content here; it decides whether tomorrow's battle can happen.</paragraph><paragraph>Item names and descriptions are rewritten around early-war Joseon logistics, messages, and defensive preparation.</paragraph>",
    ),
    (
        "Joseon's Counterattack",
        "<paragraph>The counterattack does not begin with a grand victory. It begins when a wounded man is brought in, wet powder is dried, a grain ledger is restored, and a false dispatch is exposed.</paragraph><paragraph>Dawn of Dongnae is not a story about erasing defeat. It is about rebuilding order inside defeat until resistance becomes an operation.</paragraph>",
    ),
]

KO_ITEM_NAMES = {
    "weapon": ["동래 장검", "부산진 환도", "의병 쇠몽둥이", "성문 수비창", "야습 단검", "왜군 노획도", "봉수대 활", "남문 장궁"],
    "armor": ["동래 방호복", "의병 누비갑", "성문 수비 두정갑", "피난길 덧옷", "남해 전령복", "관아 보급 갑옷", "붉은 띠 전투복", "산성 방한복"],
    "document": ["동래성 장계", "남해 수군 봉서", "봉수 암호문", "군량 장부", "피난로 지도", "왜군 척후 보고", "관아 비상 명령", "의병 연명장"],
    "food": ["전시 주먹밥", "마른 곡식 꾸러미", "소금물 가죽병", "피난민 보리죽", "산성 말린 고기", "전령용 곶감", "군량 떡", "우물가 물통"],
    "recipe": ["방습 화약 처방", "상처 세척 탕약", "활시위 손질법", "봉화 기름 배합", "전시 죽 조리법", "야간 전령 식량표"],
    "misc": ["봉화 기름병", "나루터 열쇠", "대장간 쇠못", "의병의 붉은 띠", "젖은 활시위", "산성 물표", "피 묻은 봉인", "정찰 표식"],
}

EN_ITEM_NAMES = {
    "weapon": ["Dongnae Longsword", "Busanjin Hwando", "Militia Iron Club", "Gate Guard Spear", "Night-Raid Dagger", "Captured Enemy Blade", "Beacon-Post Bow", "South Gate War Bow"],
    "armor": ["Dongnae Guarded Coat", "Militia Padded Armor", "Gate Guard Brigandine", "Refugee Road Overcoat", "Southern Courier Coat", "Magistracy Supply Armor", "Red-Sash Battle Coat", "Hill-Fort Winter Coat"],
    "document": ["Dongnae Dispatch", "Letter to the Southern Fleet", "Beacon Cipher", "Supply Ledger", "Refugee Route Map", "Enemy Scout Report", "Emergency Magistracy Order", "Militia Oath Roll"],
    "food": ["Wartime Rice Ball", "Dried Grain Bundle", "Salt-Water Skin", "Refugee Barley Porridge", "Hill-Fort Dried Meat", "Courier Persimmons", "Army Rice Cake", "Wellside Water Jar"],
    "recipe": ["Powderproofing Formula", "Wound-Washing Decoction", "Bowstring Care Notes", "Beacon Oil Mixture", "Wartime Porridge Method", "Night Courier Ration List"],
    "misc": ["Beacon Oil Flask", "Ferry Key", "Forge Nails", "Militia Red Sash", "Wet Bowstring", "Hill-Fort Water Token", "Blood-Marked Seal", "Scout Mark"],
}

KO_ITEM_DESCRIPTIONS = {
    "weapon": "전쟁 초반의 급박한 지상전에서 쓰기 위해 손질한 무기입니다. 완벽한 명품은 아니지만, 성문과 산길을 버티는 데 필요한 무게와 신뢰가 있습니다.",
    "armor": "조선 남부 방어선의 급조 장비를 본뜬 전시 복장입니다. KCD2의 기존 의복 위에 조선 방어전의 역할과 이름을 입혔습니다.",
    "document": "봉인이 살아 있어야 의미가 있는 문서입니다. 잃어버리면 사람보다 빠르게 소문이 죽고, 길보다 먼저 전선이 무너집니다.",
    "food": "피난민과 전령, 성문 수비병에게 나누기 위해 준비한 전시 식량입니다. 오래 버티기보다 지금 쓰러지지 않게 하는 데 목적이 있습니다.",
    "recipe": "전쟁 초기의 야전 제작법입니다. 화약, 붕대, 활시위, 봉화 기름처럼 작은 물자가 하루의 방어를 좌우합니다.",
    "misc": "장계와 봉수, 보급로를 살리기 위한 전시 물자입니다. 싸움이 시작되기 전부터 이미 전쟁의 방향을 바꾸는 물건입니다.",
}

EN_ITEM_DESCRIPTIONS = {
    "weapon": "A weapon prepared for urgent land fighting in the opening days of the war. It is not a perfect masterpiece, but it has the weight and reliability needed at gates and hill roads.",
    "armor": "A wartime outfit inspired by the southern Joseon defense line. Existing KCD2 clothing is reframed with a Joseon land-front role and identity.",
    "document": "A document that matters only while its seal survives. Lose it, and news dies faster than men and the line collapses before the road does.",
    "food": "Wartime food prepared for refugees, couriers, and gate guards. It is meant less for comfort than for keeping people upright today.",
    "recipe": "A field recipe for the first days of war. Powder, bandages, bowstrings, and beacon oil can decide whether a defense holds for one more day.",
    "misc": "A wartime object for keeping dispatches, beacons, and supply roads alive. The war can turn before the fighting begins.",
}

KO_CHARACTERS = [
    ("전령 한결", "동래성으로 장계를 들고 뛰는 젊은 전령입니다. 싸움보다 길을 읽는 법을 먼저 배웠지만, 전쟁 첫날부터 검을 들어야 했습니다."),
    ("수비장 박의준", "성문 앞 병사들을 다시 세우는 장수입니다. 그는 큰 승리를 약속하지 않고, 다음 봉수가 오를 때까지 버티자고 말합니다."),
    ("의병장 윤서", "세 마을의 의병을 하나의 야간 신호 아래 묶으려는 인물입니다. 관군을 쉽게 믿지 않지만, 백성을 버리지 않습니다."),
    ("봉수군 매월", "밤하늘의 불빛으로 전선을 잇는 봉수군입니다. 그녀는 말보다 연기를 믿고, 연기보다 살아 돌아온 사람을 믿습니다."),
    ("대장장이 길상", "젖은 활촉과 부러진 칼을 다시 쓰게 만드는 장인입니다. 대장간의 불도 전장에서는 봉화가 됩니다."),
    ("남해 연락관", "이순신 장군의 수군영과 육지 전선을 잇는 연락관입니다. 바다의 승리를 땅에서 먼저 준비해야 한다고 믿습니다."),
]

EN_CHARACTERS = [
    ("Courier Han-gyeol", "A young courier carrying dispatches toward Dongnae. He learned roads before swordplay, but the first day of war forced a blade into his hand."),
    ("Gate Captain Park Ui-jun", "A commander who rebuilds the line at the gate. He does not promise a grand victory; he asks the men to hold until the next beacon rises."),
    ("Militia Leader Yun Seo", "A local leader trying to bind three village militias under one night signal. He distrusts regular officers, but never abandons civilians."),
    ("Beacon Keeper Mae-wol", "A watch keeper who links the front with fire in the night sky. She trusts smoke more than speeches, and survivors more than smoke."),
    ("Smith Gil-sang", "A craftsman who makes wet arrowheads and broken blades usable again. In war, a forge fire is a beacon too."),
    ("Southern Fleet Liaison", "A messenger between Admiral Yi's naval camp and the land front. He believes the sea victory must first be protected on land."),
]

KO_TRAITS = [
    ("전령의 숨", "장계를 품은 동안 더 오래 달릴 수 있습니다. 그러나 쓰러지면 소식도 함께 멈춥니다."),
    ("성문 방어", "좁은 길과 문 앞에서 버틸 때 사기가 오릅니다."),
    ("남해의 약속", "이순신 장군이 살아 있다는 소식이 병사들의 등을 곧게 세웁니다."),
    ("의병의 맹세", "민가를 지킬 때 설득과 명성이 조금 더 힘을 얻습니다."),
    ("젖은 화약", "비바람 속에서는 원거리 전투가 흔들립니다. 준비된 자만 쏠 수 있습니다."),
    ("반격의 불씨", "작은 승리가 이어질수록 다음 전투의 두려움이 줄어듭니다."),
]

EN_TRAITS = [
    ("Courier's Breath", "While carrying a dispatch, you can push farther. If you fall, the message falls with you."),
    ("Gate Defense", "Morale rises when holding narrow roads and gates."),
    ("Promise of the Southern Sea", "News that Admiral Yi lives stiffens the backs of tired soldiers."),
    ("Militia Oath", "When protecting villages, persuasion and reputation carry more weight."),
    ("Wet Powder", "Rain unsettles ranged combat. Only the prepared can fire."),
    ("Spark of Counterattack", "Small victories make the next battle less frightening."),
]

STARTER_ITEMS = [
    ("keyring", "1"),
    ("bandage_classic", "6"),
    ("wineskin_rustic", "1"),
    ("appleDried", "4"),
    ("loot_sackOfNails", "1"),
    ("recipe_healthSmallPotion", "1"),
]


def load_zip_entries(path: Path) -> dict[str, bytes]:
    if not path.exists():
        return {}
    with zipfile.ZipFile(path, "r") as archive:
        return {entry.filename: archive.read(entry.filename) for entry in archive.infolist() if not entry.is_dir()}


def write_zip_entries(path: Path, entries: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pak", dir=path.parent) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_STORED) as archive:
            for name in sorted(entries):
                archive.writestr(name, entries[name])
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def table_xml_to_bytes(root: ET.Element) -> bytes:
    return ET.tostring(root, encoding="utf-8", xml_declaration=False)


def cells(row: ET.Element) -> list[ET.Element]:
    return list(row.findall("Cell"))


def set_row(row: ET.Element, en_text: str, localized_text: str) -> bool:
    row_cells = cells(row)
    if len(row_cells) < 3:
        return False
    row_cells[1].text = en_text
    row_cells[2].text = localized_text
    return True


def index_for(value: str, count: int) -> int:
    return sum(ord(ch) for ch in value) % count


def category_for_item(row_id: str) -> str:
    folded = row_id.lower()
    if "recipe" in folded or "skillbook" in folded or folded.startswith("alch_"):
        return "recipe"
    if any(token in folded for token in ("sword", "axe", "mace", "club", "bow", "arrow", "shield", "weapon", "polearm", "crossbow", "dagger")):
        return "weapon"
    if any(token in folded for token in ("cap", "hood", "gambeson", "tunic", "armor", "armour", "mail", "coif", "helmet", "boots", "shoes", "coat", "caftan", "waffenrock", "gloves", "hose", "cuirass", "brigandine")):
        return "armor"
    if any(token in folded for token in ("letter", "book", "map", "ledger", "dispatch", "order", "scroll", "charter", "codex")):
        return "document"
    if any(token in folded for token in ("apple", "bread", "meat", "beer", "wine", "water", "grain", "food", "beef", "perch", "rabbit", "herring", "potion")):
        return "food"
    return "misc"


def semantic_item_name(row_id: str, language: str) -> tuple[str, str] | None:
    folded = row_id.lower()
    ko = language == "ko"
    rules = [
        (("longsword", "long_sword"), ("Dongnae Longsword", "동래 장검")),
        (("shortsword", "hunting_sword", "huntingsword", "sabre", "sword"), ("Busanjin Hwando", "부산진 환도")),
        (("bow",), ("Beacon-Post Bow", "봉수대 활")),
        (("arrow",), ("Dongnae Arrow Bundle", "동래 화살 묶음")),
        (("crossbow", "bolt"), ("Captured Enemy Crossbow", "노획 쇠뇌")),
        (("shield",), ("Gate Guard Shield", "성문 수비 방패")),
        (("polearm", "spear", "voulge", "halberd"), ("Gate Guard Spear", "성문 수비창")),
        (("axe",), ("Militia Wood Axe", "의병 전투도끼")),
        (("mace", "club", "hammer", "warhammer"), ("Militia Iron Club", "의병 쇠몽둥이")),
        (("dagger", "knife"), ("Night-Raid Dagger", "야습 단검")),
        (("gambeson", "brigandine", "mail", "cuirass", "armor", "armour"), ("Militia Padded Armor", "의병 누비갑")),
        (("caftan", "coat", "tunic", "waffenrock"), ("Southern Courier Coat", "남해 전령복")),
        (("cap", "hood", "coif", "helmet", "skullcap"), ("Beacon Watch Cap", "봉수군 두건")),
        (("boots", "shoes", "hose"), ("Hill-Fort March Gear", "산성 행군 장비")),
        (("letter", "dispatch", "order"), ("Sealed Front Dispatch", "봉인 장계")),
        (("map",), ("Refugee Route Map", "피난로 지도")),
        (("ledger",), ("Supply Ledger", "군량 장부")),
        (("book", "codex", "skillbook"), ("Field Manual", "야전 교범")),
        (("recipe",), ("Powderproofing Formula", "방습 화약 처방")),
        (("bandage",), ("Wartime Bandage Roll", "전시 붕대 꾸러미")),
        (("water", "wineskin"), ("Salt-Water Skin", "소금물 가죽병")),
        (("apple", "bread", "meat", "grain", "food", "beef", "perch", "rabbit", "herring"), ("Wartime Ration", "전시 군량")),
        (("key",), ("Ferry Key", "나루터 열쇠")),
        (("nail",), ("Forge Nails", "대장간 쇠못")),
    ]
    for tokens, values in rules:
        if any(token in folded for token in tokens):
            return values[0], values[1] if ko else values[0]
    return None


def patch_items(raw: bytes, language: str) -> tuple[bytes, int]:
    root = ET.fromstring(raw)
    names = KO_ITEM_NAMES if language == "ko" else EN_ITEM_NAMES
    descs = KO_ITEM_DESCRIPTIONS if language == "ko" else EN_ITEM_DESCRIPTIONS
    changed = 0
    for row in root.findall("./Row"):
        row_cells = cells(row)
        if len(row_cells) < 3:
            continue
        row_id = row_cells[0].text or ""
        category = category_for_item(row_id)
        idx = index_for(row_id, len(names[category]))
        semantic = semantic_item_name(row_id, language)
        if row_id.startswith("ui_nm_") or row_id.endswith("_uin") or "_uin_" in row_id:
            if semantic:
                en_value, localized_value = semantic
            else:
                en_value = EN_ITEM_NAMES[category][idx]
                localized_value = names[category][idx]
        elif row_id.startswith("ui_in_") or row_id.endswith("_uii") or "_uii_" in row_id or "_desc" in row_id.lower() or "_step_" in row_id.lower():
            en_value = EN_ITEM_DESCRIPTIONS[category]
            localized_value = descs[category]
        else:
            en_value = EN_ITEM_NAMES[category][idx]
            localized_value = names[category][idx]
        if set_row(row, en_value, localized_value):
            changed += 1
    return table_xml_to_bytes(root), changed


def patch_soul(raw: bytes, language: str) -> tuple[bytes, int]:
    root = ET.fromstring(raw)
    chars = KO_CHARACTERS if language == "ko" else EN_CHARACTERS
    traits = KO_TRAITS if language == "ko" else EN_TRAITS
    changed = 0
    for row in root.findall("./Row"):
        row_cells = cells(row)
        if len(row_cells) < 3:
            continue
        row_id = row_cells[0].text or ""
        folded = row_id.lower()
        if folded.startswith("char_"):
            name, desc = chars[index_for(row_id, len(chars))]
            en_name, en_desc = EN_CHARACTERS[index_for(row_id, len(EN_CHARACTERS))]
            if folded.endswith("_uiname") or folded.endswith("_fullname"):
                changed += int(set_row(row, en_name, name))
            elif any(token in folded for token in ("description", "history", "physicaldescription", "migration", "other", "protection")):
                changed += int(set_row(row, en_desc, desc))
        elif folded.startswith("perk_") or folded.startswith("buff_"):
            name, desc = traits[index_for(row_id, len(traits))]
            en_name, en_desc = EN_TRAITS[index_for(row_id, len(EN_TRAITS))]
            if "desc" in folded or "lore" in folded:
                changed += int(set_row(row, en_desc, desc))
            else:
                changed += int(set_row(row, en_name, name))
    return table_xml_to_bytes(root), changed


def patch_codex(raw: bytes, language: str) -> tuple[bytes, int]:
    root = ET.fromstring(raw)
    codex = KO_CODEX if language == "ko" else EN_CODEX
    changed = 0
    for row in root.findall("./Row"):
        row_cells = cells(row)
        if len(row_cells) < 3:
            continue
        row_id = row_cells[0].text or ""
        if not row_id.startswith("ui_codex_"):
            continue
        title, body = codex[index_for(row_id, len(codex))]
        en_title, en_body = EN_CODEX[index_for(row_id, len(EN_CODEX))]
        if row_id.endswith("_name") or len((row_cells[1].text or "")) < 90:
            changed += int(set_row(row, en_title, title))
        else:
            changed += int(set_row(row, en_body, body))
    return table_xml_to_bytes(root), changed


def build_inventory_player_xml() -> bytes:
    item_lines = "\n".join(
        f'\t\t\t<PresetItem Name="{name}" Amount="{amount}" />' for name, amount in STARTER_ITEMS
    )
    xml = f'''<?xml version="1.0" encoding="us-ascii"?>
<database xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="barbora" xsi:noNamespaceSchemaLocation="InventoryPreset.xsd">
\t<InventoryPresets version="2">
\t\t<InventoryPreset Name="inventory_player_bohuta">
\t\t\t<InventoryPresetRef Name="inventory_tneb_bohuta" />
\t\t\t<PresetItem Name="keyring" Amount="1" />
\t\t</InventoryPreset>
\t\t<InventoryPreset Name="inventory_player_henry">
\t\t\t<ClothingPresetRef Name="joseon_counterattack_courier" />
\t\t\t<WeaponPresetRef Name="joseon_counterattack_land_front_weapons" />
{item_lines}
\t\t</InventoryPreset>
\t</InventoryPresets>
</database>
'''
    return xml.encode("ascii")


def build_clothing_preset_xml() -> bytes:
    xml = '''<?xml version="1.0" encoding="us-ascii"?>
<database xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="barbora" xsi:noNamespaceSchemaLocation="../database.xsd">
\t<clothing_presets version="2">
\t\t<clothing_preset clothing_preset_id="7b45f0b8-b16a-426f-9a7b-02a150ea1592" clothing_preset_name="joseon_counterattack_courier" gender="Male" prefers_hood_on="true" Quality="2" Condition="0.92">
\t\t\t<Items>
\t\t\t\t<Guid>01894921-14e0-4012-a3a6-5f1fcf01d2d2</Guid>
\t\t\t\t<Guid>3694c855-086f-4ce4-b402-a97ecce944f9</Guid>
\t\t\t\t<Guid>018c1614-ddbf-4d9b-a797-40330be86c1c</Guid>
\t\t\t\t<Guid>003c862e-e1a9-480b-80b9-be6a2ccf055f</Guid>
\t\t\t</Items>
\t\t</clothing_preset>
\t</clothing_presets>
</database>
'''
    return xml.encode("ascii")


def build_weapon_preset_xml() -> bytes:
    xml = '''<?xml version="1.0" encoding="us-ascii"?>
<database xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" name="barbora" xsi:noNamespaceSchemaLocation="../database.xsd">
\t<weapon_presets version="1">
\t\t<weapon_preset weapon_preset_id="f77b8f25-912f-48a6-9ce3-0b2f40e71592" weapon_preset_name="joseon_counterattack_land_front_weapons" Quality="2" Condition="0.92">
\t\t\t<weapon_preset_item item_class_id="059893ea-3aef-48b3-b1ce-7eb3391fa028" />
\t\t\t<weapon_preset_item item_class_id="0077dfa2-b9be-4ae3-ae59-2803ba49dfcb" />
\t\t\t<weapon_preset_item item_class_id="710e3706-8974-404b-b23a-6f51670ef1ed" amount="60" />
\t\t\t<weapon_preset_item item_class_id="2cb53d10-c5da-47ef-8789-8e1ae34dac6c" />
\t\t</weapon_preset>
\t</weapon_presets>
</database>
'''
    return xml.encode("ascii")


def build_storm_player_xml() -> bytes:
    xml = '''<?xml version="1.0"?>
<!DOCTYPE storm SYSTEM "..\\storm.dtd">
<storm>
\t<rules>
\t\t<rule name="inventory_player_henry_joseon_counterattack" Mode="and">
\t\t\t<selectors>
\t\t\t\t<hasName name="player_henry"/>
\t\t\t</selectors>
\t\t\t<operations>
\t\t\t\t<setInventory preset="inventory_player_henry" />
\t\t\t</operations>
\t\t</rule>
\t\t<rule name="inventory_cutscene_really_naked_henry" Mode="and">
\t\t\t<selectors>
\t\t\t\t<hasName name="cutscene_really_naked_henry"/>
\t\t\t</selectors>
\t\t\t<operations>
\t\t\t\t<setInventory preset="inventory_empty" />
\t\t\t</operations>
\t\t</rule>
\t\t<rule name="inventory_player_bohuta" Mode="and">
\t\t\t<selectors>
\t\t\t\t<hasName name="player_bohuta"/>
\t\t\t</selectors>
\t\t\t<operations>
\t\t\t\t<setInventory preset="inventory_player_bohuta" />
\t\t\t</operations>
\t\t</rule>
\t</rules>
</storm>
'''
    return xml.encode("utf-8")


def patch_localization(game_root: Path, build_root: Path) -> list[dict]:
    reports: list[dict] = []
    for pak_name, language in (("Korean_xml.pak", "ko"), ("English_xml.pak", "en")):
        source_pak = game_root / "Localization" / pak_name
        build_pak = build_root / "Localization" / pak_name
        source_entries = load_zip_entries(source_pak)
        build_entries = load_zip_entries(build_pak)
        for entry_name in LOCALIZATION_ENTRIES:
            base = build_entries.get(entry_name) or source_entries[entry_name]
            if entry_name in {"text_ui_items.xml", "text_ui_soul.xml"}:
                base = source_entries[entry_name]
            if entry_name == "text_ui_items.xml":
                patched, changed = patch_items(base, language)
            elif entry_name == "text_ui_soul.xml":
                patched, changed = patch_soul(base, language)
            else:
                patched, changed = patch_codex(base, language)
            build_entries[entry_name] = patched
            reports.append({"kind": "localization_deep", "pak": pak_name, "entry": entry_name, "rowsChanged": changed})
        write_zip_entries(build_pak, build_entries)
    return reports


def patch_data(build_root: Path, mod_id: str) -> list[dict]:
    pak_path = build_root / "Data" / f"{mod_id}.pak"
    entries = load_zip_entries(pak_path)
    data_entries = {
        "Libs/Tables/item/InventoryPreset__player.xml": build_inventory_player_xml(),
        "Libs/Tables/item/clothing_preset__joseon_counterattack_early.xml": build_clothing_preset_xml(),
        "Libs/Tables/item/weapon_preset__joseon_counterattack_early.xml": build_weapon_preset_xml(),
        "Libs/Storm/equipment/player.xml": build_storm_player_xml(),
    }
    entries.update(data_entries)
    write_zip_entries(pak_path, entries)
    return [
        {"kind": "data_deep", "pak": f"{mod_id}.pak", "entry": name, "bytes": len(payload)}
        for name, payload in data_entries.items()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-root", required=True)
    parser.add_argument("--build-root", required=True)
    parser.add_argument("--mod-id", required=True)
    args = parser.parse_args()

    game_root = Path(args.game_root)
    build_root = Path(args.build_root)
    reports = patch_localization(game_root, build_root)
    reports.extend(patch_data(build_root, args.mod_id))
    report = {"status": "ok", "reports": reports}
    report_path = build_root / "deep-content-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
