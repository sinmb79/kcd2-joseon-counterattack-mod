# KCD2 조선의 반격 초기전 모드

[English](README.en.md)

이 폴더는 보스 PC에 설치된 `Kingdom Come: Deliverance II`에 적용되는 로컬 팬픽 모드입니다. KCD2 원본 파일을 직접 덮어쓰지 않고, 공식 수동 모드 구조인 `Mods/<modid>` 아래에 별도 패키지를 배치합니다.

## 방향

- 시작 시점: 1592년 임진왜란 초반
- 중심 무대: 부산진, 동래성, 남부 내륙 방어선, 보급로
- 플레이 감각: 해상전이 아니라 KCD2에 맞는 지상전, 정찰, 수송, 야간 침투, 방어전
- 핵심 원칙: 이순신 장군은 살아 있으며, 해상 전략망은 배경 압력과 희망의 축으로 유지
- 권리 경계: 다른 상용 게임의 이미지와 캐릭터 파일은 배포하지 않음

## 설치 위치

```text
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Mods\joseon_counterattack_early
```

## 빌드와 검증

```powershell
cd "C:\Users\sinmb\Documents\New project 2\imjin-war-joseon-counterattack-story-lab"
.\kcd2_mod\scripts\build_and_install.ps1
.\kcd2_mod\scripts\verify_install.ps1
```

검증이 성공하면 `status: ok`가 출력됩니다. 검증 대상은 다음입니다.

- `Localization\Korean_xml.pak`
- `Localization\English_xml.pak`
- `Data\joseon_counterattack_early.pak`
- `text_ui_menus.xml`
- `text_ui_tutorials.xml`
- `text_ui_quest.xml`
- `text_ui_items.xml`
- `text_ui_soul.xml`
- `Libs/Tables/item/InventoryPreset__player.xml`
- `Libs/Tables/item/clothing_preset__joseon_counterattack_early.xml`
- `Libs/Tables/item/weapon_preset__joseon_counterattack_early.xml`
- `Libs/Tables/rpg/rpg_param__joseon_counterattack_early.xml`

## 심화 적용 내용

- 코덱스: `ui_codex_*` 행을 임진왜란 초반, 부산진/동래성, 이순신 생존 원칙, 장계/봉수, 의병/관군 재편 중심으로 재작성
- 아이템: 검, 활, 방패, 문서, 식량, 제작법을 `동래 장검`, `봉수대 활`, `성문 수비 방패`, `방습 화약 처방` 같은 조선 초기전 이름과 설명으로 재분류
- 캐릭터/특성: 주요 인물과 특성을 `수비장 박의준`, `전령 한결`, `남해의 약속`, `반격의 불씨` 같은 세계관 용어로 치환
- 시작 장비: 플레이어 인벤토리에 전령/수비병용 복식, 무장, 화살, 붕대, 물통, 비상 식량, 제작법을 넣음

## 조선의 반격 이미지 브리지

보스 PC에는 `임진왜란 조선의 반격`이 다음 위치에 설치되어 있습니다.

```text
C:\Program Files (x86)\Joycity\ImjinWar
```

다음 스크립트는 그 설치본에서 Unity Texture2D/TextAsset을 로컬 전용 폴더로 추출하고, KCD2가 읽을 수 있는 private UI PAK를 모드 폴더에 생성합니다.

```powershell
.\kcd2_mod\scripts\build_private_imjinwar_bridge.ps1
.\kcd2_mod\scripts\verify_private_imjinwar_bridge.ps1
.\kcd2_mod\scripts\verify_visual_asset_pack.ps1
```

생성 위치:

```text
assets\game-captures-private\imjinwar_extract\
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Mods\joseon_counterattack_early\Data\joseon_counterattack_private_ui.pak
```

이 파일들은 보스 PC에서 실제 플레이할 때만 쓰이며, 공개 저장소에는 올라가지 않습니다.

확장 비주얼 팩은 같은 private PAK 안에 조선풍 아이콘, 코덱스 배경, 지도, 성문/봉수/시장 배경, 그리고 한옥 회벽·석축·목재·한지창 도시 재질을 함께 넣습니다. 현재 검증 기준은 54개 DDS 엔트리입니다.

## 공식 에디터

공식 모딩툴은 Steam 도구 앱으로 설치되어 있습니다.

```text
C:\Program Files (x86)\Steam\steamapps\common\KCD2Mod
```

에디터 실행:

```powershell
.\kcd2_mod\scripts\launch_editor.ps1
```

`Database system error`가 뜨면 본편 PAK 연결이 빠진 것입니다. 아래 스크립트로 복구합니다.

```powershell
.\kcd2_mod\scripts\setup_editor_workspace.ps1
```

## 구조

```mermaid
flowchart TD
  A["patches/localization_overrides.json"] --> B["build_and_install.ps1"]
  C["patches/long_campaign_overrides.json"] --> B
  D["patches/gameplay_overrides.json"] --> B
  I["tools/kcd2_deep_content_patch.py"] --> B
  B --> E["KCD2 Mods 폴더"]
  J["build_visual_asset_pack.ps1"] --> E
  F["setup_editor_workspace.ps1"] --> G["KCD2Mod 에디터 워크스페이스"]
  G --> H["WARHORSE Sandbox Editor"]
```

## 현재 한계

이 버전은 플레이 가능한 로컬 모드 패키지, 에디터 환경, 그리고 조선의 반격 로컬 이미지 브리지를 완성한 단계입니다. 캐릭터 모델, 복식, 무기 외형 전체 교체는 공식 에디터와 별도 자산 파이프라인에서 계속 확장할 수 있습니다. 공개 저장소에는 상용 게임 자산을 포함하지 않습니다.
