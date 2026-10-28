# Optional experimental installation and restore

The package has **not** been installed automatically. It contains text resources only. Native Arabic progressive reveal remains unresolved, so this is not the final Arabic localization requested.

From the workspace, after building:

```powershell
python scripts/install.py --experimental-text-only --game-root "<Steam library>\steamapps\common\Dispatch"
```

The installer checks the package checksum, then refuses any game whose executable SHA256 and original pak sizes are not listed in `compatibility/game_build.json` (Dispatch 1.0.19512, Steam build 25637711). `--dry-run` performs every check and writes nothing. It then adds only:

`<game root>\Dispatch\Content\Paks\Dispatch_AR_Texts_P.pak`

It refuses to overwrite an unknown or externally modified file with that name. Its ownership/checksum state is saved in `backups/installation_state.json`; a replaced previous installer-owned text PAK is backed up. Reinstalling identical bytes is harmless. No original PAK, font, executable, configuration, save or privacy setting is changed. No game is launched.

Arabic culture must be requested separately at a future user-controlled launch, for example `-culture=ar`. The current package does not add a new Arabic option to the game's language-selection UI. Native culture activation and possible reset by game settings remain unverified. This instruction is not an instruction to launch during the current task.

Remove only the installer-owned text package:

```powershell
python scripts/install.py --uninstall --game-root "<Steam library>\steamapps\common\Dispatch"
```

Removal requires the current file to match its recorded hash and fixed destination. It does not delete unknown/modified data. Original resources need no restoration because they were never replaced.

`python scripts/install.py --selftest` exercises fake files under a verified temporary test directory, including idempotency, refusal to delete foreign changes and unchanged original sentinels. It never installs into the actual game.
