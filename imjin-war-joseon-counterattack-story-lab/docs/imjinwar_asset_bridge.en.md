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
```

Generated local outputs:

```text
assets\game-captures-private\imjinwar_extract\
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2\Mods\joseon_counterattack_early\Data\joseon_counterattack_private_ui.pak
```

The private PAK maps selected Unity textures into existing KCD2 UI DDS paths so parts of the quest/book/item/buff UI can pick up a Joseon Counterattack visual tone locally.
