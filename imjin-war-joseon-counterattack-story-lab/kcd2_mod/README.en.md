# KCD2 Joseon Counterattack Early Front Mod

This folder prepares a non-destructive fan mod for the locally installed `Kingdom Come: Deliverance II` game.

The current build does not redistribute or copy assets from another commercial game. Instead, it generates a local KCD2 mod from the user's own installed files and applies an early Imjin War Joseon land-defense tone through localization overrides.

## Design Rules

- Start in the opening phase of the Imjin War, around the Busanjin and Dongnae pressure.
- Keep Admiral Yi Sun-sin alive.
- Treat the navy as a living strategic background force, while gameplay tone stays land-combat focused.
- Install through KCD2's manual mod structure: `Mods/<modid>/mod.manifest` plus packed `.pak` files.
- Do not publish repacked KCD2 localization or third-party game assets.

## Run

Open PowerShell as administrator and run:

```powershell
.\kcd2_mod\scripts\build_and_install.ps1
.\kcd2_mod\scripts\verify_install.ps1
```

Default game path:

```text
C:\Program Files (x86)\Steam\steamapps\common\KingdomComeDeliverance2
```
