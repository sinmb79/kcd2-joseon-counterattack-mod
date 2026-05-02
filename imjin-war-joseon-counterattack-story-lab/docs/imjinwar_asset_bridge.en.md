# ImjinWar Asset Bridge

[한국어](imjinwar_asset_bridge.md)

The installed `Imjin War: Joseon Counterattack` client was found here:

```text
C:\Program Files (x86)\Joycity\ImjinWar
```

It is a Unity/IL2CPP game. Images and text live under `IMClient\ImjinWar_Data` as Unity `assets`, `resS`, and Addressables data.

## Local-Only Workflow

Commercial game assets are not committed to the public repository. The bridge extracts them only on this PC:

```powershell
.\kcd2_mod\scripts\build_private_imjinwar_bridge.ps1
.\kcd2_mod\scripts\verify_private_imjinwar_bridge.ps1
.\kcd2_mod\scripts\verify_visual_asset_pack.ps1
```

Generated local outputs:

```text
assets\game-captures-private\imjinwar_extract\
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Mods\joseon_counterattack_early\Data\joseon_counterattack_private_ui.pak
```

The private PAK maps selected Unity textures into existing KCD2 UI DDS paths so parts of the quest/book/item/buff UI can pick up a Joseon Counterattack visual tone locally.

The expanded visual-pack stage creates original Joseon-style item icons, maps, and document images. The default `safe` profile installs only 20 DDS entries and avoids broad UI or city-material overrides, because blanket material replacement can make the live game look broken. The broader 54-entry `full` profile remains experimental and must be requested explicitly.
