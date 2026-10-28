# R8b repair — round 019

Result: **R8B_REPAIR_READY** (offline only). The Run 2 frame bug is repaired, the validators pass, and the staging pak is
ready. Nothing was installed, and the game was not run. `IN_GAME_RTL_PROVEN=false`, `final=0`.

## Defect (round 017, not re-investigated)

`Set Displayed Line` instruction 66 is a bare `EX_LocalFinalFunction Build Arabic Timing(ARPlain, ARSpeaker)`.
`Build Arabic Timing` is a clone of `Build Arabic Markup` that kept `ReturnValue: StrProperty (CPF_Parm|CPF_OutParm|CPF_ReturnParm)`,
`FUNC_HasOutParms` and `Return Local(Output)`. For a top-level statement, `ProcessLocalScriptFunction` passes its uninitialized
64-byte scratch buffer as `RESULT_PARAM`. The FString copy then wrote the markup over caller locals and the live FFrame
(`FFrame.Code` = UTF-16 text = fault Rax). Proven against the Run 2 minidump (`r8b_dump_frame_017.json`).

## Repair (void helper)

Static inspection confirmed that the void repair preserves semantics:
- The only call site of `Build Arabic Timing` in the package is the Run 2 statement, so nothing consumes the string.
- The function's effects are `ArabicUnitDelays` (SetArray plus `Array_Add`), `ArabicUnitCount` and `ArabicSpeakerUnits`.
- The function has exactly one `Return`, at instruction 83 followed by `EndOfScript`, and no jump targets it.

`RepairTiming019` (`tools/asset_inspector/ArabicRepair019.cs`) therefore makes three changes:
1. Removes the `ReturnValue` FStrProperty.
2. Clears `FUNC_HasOutParms`; no `CPF_OutParm` remains.
3. Replaces `Return Local(Output)` with `Return Nothing`, using the project assembler (label relocation, size recomputation).

The `Output` local is still built and discarded, which is harmless (locals are destroyed at frame exit).

| Field | Before (012 = installed 014) | After (019) |
|---|---|---|
| FunctionFlags | Public, **HasOutParms**, HasDefaults, BlueprintCallable, BlueprintEvent | Public, HasDefaults, BlueprintCallable, BlueprintEvent |
| PropertiesSize / ParmsSize / NumParms | 216 / 48 / 3 | 200 / 32 / 2 |
| ReturnValueOffset | 32 (FString) | MAX_uint16 |
| Parameters | Content@0, Speaker@16 (CPF_Parm), ReturnValue@32 | Content@0, Speaker@16 (CPF_Parm) |
| Locals | 19, Input@48 … DiscardedArrayIndex@212 | same 19, same order, each offset −16 |
| ElementSize / ArrayDim | equal to runtime size / 1 | equal to runtime size / 1 |
| ScriptBytecodeSize (logical) | 2893 | 2885 (−8: one FField* operand) |
| Serialized bytecode | 4049 B, 85 instructions | 4033 B, 85 instructions |
| Return | instr 83 `Return Local(Output)` | instr 83 `Return Nothing` |
| Property operands in bytecode | 20 names, all resolve | same 20 names, all resolve; `ReturnValue` never referenced |

Machine-readable before/after record: `r8b_repair_019/frame_audit_019.json` (`metadata`, `checks`, `layouts`).
Offsets come from the round-017 UStruct::Link model, which was validated against the Run 2 dump. Nothing is guessed.

## Artifact

`builds/rtl_poc/r8b_repair_019/WBP_SubtitleBlock_AR_R8B_REPAIR_019.{uasset,uexp}`, labelled OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED.
- uasset `e4189ec226170f487ed232ebc0a4659fa559d91738a2aea6d59f892cd02b6f52`
- uexp `9ab47d953df90f163689203abb356ccd81ce2828c7a4898ea762f49b4e24b0b4`

Build route, from clean source:
1. Start from the frozen 011 pair (hash-gated).
2. Apply `RepairTiming019`.
3. Run the unchanged round-012 clock generator.

Cross-checks:
- **Equals the repair applied to the frozen 012 pair, byte for byte** (`cross_check_from_012/`).
- A second full generation is byte-identical (`determinism/`), and so is the independent dev run `r8b_repair_019_dev01`.
- A reread/rewrite is byte-identical (`roundtrip/`), so no serializer delta exists.

Against 012, 72 of 73 exports are byte-identical. Only export 66 changes: −63 bytes, being one serialized FStrProperty
(47 B) plus one EX_LocalVariable operand (16 B). NameMap and imports are identical. Earlier artifacts are untouched.

## Permanent validator rule (return contract)

`ReturnContractR` runs in `--arabic-wbp-repair-019` / `--validate-arabic-wbp-repair-019`, together with the full 012 clock validator.
- It walks every instruction of every function and propagates the VM's RESULT_PARAM destination through each construct:
  `Let`, `LetBool`, `LetObj`, `LetValueOnPersistentFrame`, `JumpIfNot`, `ComputedJump`, `Return`, `Context`
  (which forwards its destination and checks the r-value property), `SwitchValue`, `StructMemberContext`, `SetArray`,
  `StructConst`, delegates and call parameters.
- Script out-parameters receive a null destination.
- **Top-level statement:** a call may return only void, a scalar (Bool/Byte/Int*/Float/Double/Name/Object/Class/Enum), or
  a struct whose native thunk only plainly stores the result. FString, FText, TArray, Map, Set, Delegate and any other struct
  are rejected. A value expression (variable or constant) is rejected at statement level outright.
- **Typed destination:** a call result, variable or constant must have a compatible type. A void call cannot be used as a value.
- Unresolved callee signatures and argument-count mismatches are rejected.
- Native signatures come from `r8b_repair_019/native_returns_019.json`, produced by `tools/r8b_019/native_returns_019.py`.
  It reads the shipped EXE's UHT `FFunctionParams` tables and covers 64 callees: 57 unique, 4 agreeing, 3 resolved by the
  shipped compiler's binding. Struct returns are checked in the thunk itself:
  - `K2_SetTimer` thunk 0x28a0aa0: the only use of RESULT is `mov qword ptr [r14], rcx` (8 bytes).
  - Positive controls: `Conv_ColorToLinearColor` and `MakeColor`.
  - Negative controls `Concat_StrStr` and `Conv_StringToText` are classified non-trivial (the FText thunk reads the old destination).

Result on the repair: **1120 call sites, 0 invalid; 128 statement-level calls (127 void, 1 `K2_SetTimer` FTimerHandle)**
(`r8b_repair_019/return_contract_019.json`). Instruction 66 is now a void statement.

Negative fixtures, all detected (27 total = 15 inherited clock/lifecycle fixtures + 12 return-contract fixtures):
- The real Run 2 artifact (frozen 012) is rejected at exactly `Set Displayed Line:66 Build Arabic Timing -> Str`.
- Restored FString, FText, TArray and struct returns.
- A bare native FString return.
- `K2_SetTimer` without thunk evidence.
- A Let type mismatch, an argument type mismatch, and a bare value expression.
- A missing native signature.
- Positive control: a bool-returning bare call is accepted.

The independent Python audit (`tools/r8b_019/frame_audit_019.py`, 16 checks) reports **FRAME_LAYOUT_AUDIT_PASS**:
- 1120 call sites.
- Before the repair, exactly one invalid site: Set Displayed Line:66, Str. After the repair, zero.
- Only the `Build Arabic Timing` layout changed.
- All other functions are identical to 012.
- Instruction 66 is unreachable with `bArabic=false`.

The round-017 audit on the repair: 46 script call sites, 0 invalid (`frame_audit_017_rule_on_repair.json`).

## Other checks (CheckClock on the repaired baseline)

- 0 dangling FPackageIndex.
- 0 unresolved property operands.
- 0 unresolved function imports.
- 0 bad jumps and 0 bad context skips, in every function.
- 0 unexpected schema or export changes.
- Frozen name and import prefixes unchanged.
- Reveal invariants hold: idempotent Finish, one broadcast, scheduler clear, pool reset, paired shadow update, and no
  SetText or SetTextStyleSet in paced functions.
- Clock semantics hold.
- No EDL dependency cycle.

Replay (`tools/asset_inspector/test_repair_019.py`):
- The void helper returns None, and its ledger, unit count and speaker units equal the canonical segmenter on 96 fixtures.
  `Build Arabic Markup` is unchanged.
- AWP=false: 500/500 frame-identical to NativeProto. AWP=true: 500/500, max 0 frames.
- 14 lifecycle cases.
- Validator: 0 errors.

## English isolation

The English path is unchanged from the 012 build that Run 1 played in English. That is evidence of no regression; it does
not prove the pak mounted.
- Every function other than `Build Arabic Timing` is identical to 012.
- `Build Arabic Timing` is reachable only through Set Displayed Line:66, inside the `bArabic` branch: 50 instructions are
  reachable in English and 76 in Arabic, and instruction 66 is not among the English ones.
- The language gate stays `L=="ar" || StartsWith(L,"ar-")`.

## Staging pak

`builds/rtl_poc/r8b_runtime_staging_019/Dispatch_AR_R8b_P.pak`, sha256 `1058eac436c2844f44b0ca60d625dfad832296214aea9dca676d401279f1f988`, 652,628 bytes.
- Built with repak 0.2.3, V11, mount `../../../`, path-hash seed 0, uncompressed, unencrypted, `RAYON_NUM_THREADS=1`.
- Two builds are byte-identical, and both readbacks are hash-equal to the sources.
- Contents: 10 files, the same paths as the Run 2 pak (`c8f0a7f4…563c`). Only the WBP pair differs. The four DT_AR tables are byte-identical.
- No Texts, Fonts, Locmeta or TTF content.
- Not installed. The Run 5 procedure is in `RUN5_READY.md` in the same folder.

## Not proven

- In-game behaviour of the repaired renderer:
  - right-side Arabic reveal, stationary glyphs and stable joining;
  - shadow synchronization;
  - runtime widget binding;
  - RetainerBox and outline behaviour on 4.27;
  - K2_SetTimer firing in game.
- The runtime pak mount for R8b. Run 2 proved that a `_P` WBP override loads; Run 5 must show it again.
