# Proto 1.02 — bounded static binary evidence, round 002

Date: 2026-10-23 (Asia/Riyadh).

```text
PAINT_MODEL_LOGICAL_PEN
ZERO_INTERVAL_BATCHES_CHARACTERS
WORD_REVEAL_REJECTED  (timing-only approach)
ARABIC_ISOLATION_NOT_PROVEN
GAME_NOT_RUN
STEAM_NOT_RUN
PACKAGE_NOT_INSTALLED
IN_GAME_RTL_NOT_PROVEN
tested_in_game=0
final=0
```

The shipped character-run paint code constructs successive one-unit text ranges,
draws their shaped slices, and accumulates slice widths in logical index order.
Changing timing cannot correct those positions. Zero delay does batch iterations
in one processing call; it is not passed immediately to an invalid zero-rate timer
by the ordinary entry path. That favorable timing result does not rescue the paint
model. This rejects the detached timing-only POC, not every possible native fix.

## Read the evidence

- `findings.md`: registration, field offsets, provenance and decision.
- `paint_model.md`: decisive loop, geometry and shaped-range helper.
- `zero_interval.md`: zero branch, budget loop and scheduler boundary.
- `functions.json`: 21 descriptive function aliases, addresses, file offsets,
  approximate bounds, .pdata fragments, outgoing calls and important incoming xrefs.
- `xrefs.json`: selected validated pointers, calls and RIP-relative references.
- `excerpts.md`: short selected instruction windows; no executable dump.
- `results.json`: machine-readable classifications and field offsets.
- `integrity.json`: fresh full SHA256 check against the 97-file game baseline.

All addresses are RVAs unless stated otherwise. Image base: `0x140000000`.
Executable SHA256:
`365637a77d4b74a61d198a9927e3dcd437bf3be2247b96fcbe5c2e851ac14923`.
These addresses apply only to that build. No C++ symbol names were recovered;
function aliases describe roles established by the listed code/data relationships.

## Reproduce without running the game

From `C:\Dispatch_AR`:

```powershell
python -X utf8 tools/proto_binary_analysis/evidence.py
```

Uses the already installed `capstone`, `numpy`, and `pefile` via existing `pe.py`.
Reads the executable with `Path.read_bytes()` only. Writes fixed evidence outputs
inside this directory. Refuses an unknown executable hash. Checks 8 reflected
fields, 8 pointer links, 21 decoded spans and 13 decisive instruction guards.
The JSON classifications are analyst conclusions checked against this build;
the script is not a general automatic reverse-engineering classifier.

The old `disfn.py` helper reports a single .pdata range, or an arbitrary 0x200-byte
fallback for a leaf. These are not reliable full C++ function bounds. The new
evidence decodes explicitly recovered logical spans from their entry and filters
excerpts by instruction address, avoiding mid-instruction snippets and truncated
.pdata fragments. No existing helper was modified.

Public tutorials remain `PUBLIC_REFERENCE_ONLY`. No conclusion here relies on
equating the tutorial with the shipped plugin. There was no game execution,
debugging, hooking, DLL creation, injection, PAK installation or EXE patching.
