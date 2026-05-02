# 조선풍 비주얼 팩

[English](visual_asset_pack.en.md)

보스 PC의 `임진왜란 조선의 반격` 설치본에서 추출한 로컬 텍스처를 참고하고, 공개 저장소에는 상용 자산을 넣지 않는 방식으로 KCD2용 조선풍 비주얼 PAK를 만듭니다.

## 적용 위치

```text
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Mods\joseon_counterattack_early\Data\joseon_counterattack_private_ui.pak
```

## 생성 명령

```powershell
.\kcd2_mod\scripts\build_private_imjinwar_bridge.ps1
.\kcd2_mod\scripts\verify_visual_asset_pack.ps1
```

`build_private_imjinwar_bridge.ps1`는 Unity 자산을 추출한 뒤 `build_visual_asset_pack.ps1 -Profile safe`를 자동으로 호출합니다. 이미 추출이 끝난 상태에서 안전 비주얼만 다시 만들 때는 다음 명령만 실행하면 됩니다.

```powershell
.\kcd2_mod\scripts\build_visual_asset_pack.ps1
```

## 반영 범위

- 기본 안전 프로필 DDS 20개
- 환도, 봉수대 활, 성문 수비 방패, 장계, 보급 식량, 방습 화약, 전장 의약품 아이콘
- 부산진/동래성 보급로를 상상한 작전 지도와 문서 이미지
- 전역 UI, 책 장식 전체, 도시 구조물 재질은 기본값에서 덮지 않음

```mermaid
flowchart TD
  A["ImjinWar 로컬 설치본"] --> B["UnityPy 추출"]
  B --> C["private PNG 텍스처"]
  C --> D["Pillow 기반 조선풍 이미지 생성"]
  D --> E["DDS 변환"]
  E --> F["joseon_counterattack_private_ui.pak"]
  F --> G["KCD2 Mods 폴더"]
```

## 검증 결과 기준

`verify_visual_asset_pack.ps1`는 기본 안전 프로필에서 다음을 확인합니다.

- private PAK 존재
- 20개 이상 엔트리 포함
- 지도, 제품/재료 아이콘, 제작법/문서 이미지 포함
- 전역 UI와 도시 재질 오버라이드가 들어가지 않았는지 확인

생성 미리보기와 매니페스트는 Git에 올라가지 않는 로컬 전용 폴더에 저장됩니다.

```text
assets\game-captures-private\kcd2_visual_pack\
```

## 실험용 전체 프로필

`full` 프로필은 54개 DDS를 만들며 도시 재질까지 덮습니다. 실제 게임 화면이 크게 망가질 수 있으므로 기본 적용에서 제외했습니다.

```powershell
.\kcd2_mod\scripts\build_visual_asset_pack.ps1 -Profile full
.\kcd2_mod\scripts\verify_visual_asset_pack.ps1 -Profile full
```
