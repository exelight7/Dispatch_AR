# R8b WBP Stage 2 — Arabic initialization subset

2026-10-25. `R8B_WBP_STAGE2_PASS` applies to the explicitly permitted **initialization subset**.
STAGE2 / OFFLINE / NOT_INSTALLABLE / NOT_RUNTIME_TESTED. Timed reveal/Arabic Step/Arabic Finish are absent.

## Generated artifact and changes

Accepted pair: `builds/rtl_poc/stage2/WBP_SubtitleBlock_AR_STAGE2.{uasset,uexp}`.
The internal original package/class identity is retained. Stage 1 is input only; all 62 files beneath its directory
remain hash-identical. Its four Arabic tables are reused at their existing virtual paths, without regeneration.

57 exports (6 new helper functions), 128 imports (19 appended), 378 names (61 appended).
All original Stage-1 name/import indices remain fixed. Existing widget/slot/layout exports remain byte-identical.
Only original exports 11,12,22,23 change: Set Displayed Line, Stop Displaying Line, BPGC and CDO.
47/51 original payloads and all 19 untouched function payloads/raw scripts remain byte-identical; unexpected changes=0.

## Main CFG and English preservation

The shared original instructions 2..6 execute first, including the original colour/profanity calls. The new language
query immediately follows original instruction6. Its predicate is exactly `L == "ar" || StartsWith(L,"ar-")`, case-sensitive;
the emitted expression is tested for ar/ar-SA/ar-EG/arn/en/AR. No character-based routing is used.

Arabic takes the new initialization branch. English enters its original instructions 7..37, with original pushes 0/1
scoped inside that branch. The pushes retain the relocated original return/layout continuations. Original instruction
operands and side-effect order are preserved, apart from verified address relocation and an additive restore of widgets
previously suppressed by an Arabic line. Both original typewriter-enabled and ShowText flow-stack traces are checked.
Original delegates, speaker/profanity processing, Proto calls, skip/finish and pool entry functions remain on that path.

`insertion_map.json` identifies every original/shared/Arabic/new root instruction. `stage2_instruction_inventory.json`
records logical VM offsets and serialized spans. `function_diff.json` records per-export payload/script SHA256 pairs.
This is semantic English-continuation preservation, **not** whole-WBP bytecode equality or English runtime proof.

## Arabic initialization

The new callback uses the original ProcessLocalizedTextWithCallback flow with Format As Arabic Plain; it strips
only `<Italic>`/`</>`. Speaker visibility is read through the original setting calls and uses plain speaker text.
Build Arabic Markup produces the entire logical string before any Arabic SetText. It follows the canonical module's
four separators, letterless-token attachment, newline predicate, speaker segment, 37-unit cap, tail merge and escaping.
No Reverse, presentation-form conversion, visual-order conversion, partial-text rendering or Proto logical pen is used.
Character substrings are used only for logical tokenization; rendering receives the full final markup once.

Foreground selects Fill/Outline and normal/Large using Has Outline and the original Proto table-size state.
Shadow selects Fill/Fill_Large. Hidden threshold is applied to both Borders **before** the two stock RichTextBlock
SetText calls. Each receives SetText exactly once. Arabic widgets are enabled, with the shadow retainer visibility/
retention matching the original outline mode. English Proto foreground/retainer are collapsed; Arabic text is never
passed to Proto PrintLetterByLetter or ShowText. Original letterbox side effects are retained once on each path.
The initial post-SetText threshold is SpeakerUnits-1; the rest awaits the future reveal scheduler.

Stop Displaying Line retains its original hide call and adds Arabic threshold reset/root collapse when active.
The separate suppression flag permits English restoration even after a Stop/pool cycle.

## Fields, imports and helper bytecode

Six new state fields: bArabic, bArabicActive, bArabicProtoSuppressed (bool), ArabicThreshold, ArabicUnitCount,
ArabicSpeakerUnits (int). Flags CPF_BlueprintVisible/Transient; dimensions/metadata follow the existing cooked
FProperty representation. No native offsets are guessed. Function temporaries are typed function locals.

Six helpers: Format As Arabic Plain, AR Escape, AR Is Separator, AR Is Letter Code, Build Arabic Markup,
Set Threshold Arabic. The first helper clones the original callback's exact two parameter/return property definitions.
Threshold uses 37 exact float32 constants `10.5^t`, clamps at36 and writes zero when hidden; it requests both retainers.
There is no accumulated-multiplication approximation, new shader or new material.

New imports are stock string/math methods, the language library/query, Border.SetContentColorAndOpacity and
RichTextBlock.SetText. Existing methods and class imports are reused. Full lists/property metadata:
`new_variables_imports.json`. Reference validation proves package-table/property-path coherence; runtime native dispatch
and engine binding have not been executed or proven.

## Relocation and validator

The existing asset inspector now exposes `--arabic-wbp-stage2` and `--validate-arabic-wbp-stage2`.
Assembly measures VM sizes through UAssetAPI, fixes root labels and recursively relocates the absolute operands
present in the cloned expressions: CodeOffset, PushingAddress, EndGotoOffset, NextOffset/SkipOffset. Context skips are
recomputed from the measured context expression. Serialized byte offsets are never substituted for VM offsets.

The independently callable validator checks parsing/roundtrip, complete intended schema, original prefixes, variable
owners, function imports, package indices, root jump/push boundaries, exact context skip lengths, logical script sizes,
both continuation reachability, and English stack traces. Source-relative certificates independently verify cloned
nested switch destinations: unchanged expression bodies retain the original boundary's relative position, with the
measured root displacement applied. This covers the actual operand types in this package; it is not an arbitrary
Kismet decompiler for unrelated opcodes.

Generated CFGs are checked acyclic except Build Arabic Markup's explicit bounded character/token/phase loops.
Those loops advance cursor/scan or move from speaker to content; a bounded instruction evaluator checks their outputs.
English execution-flow push/pop semantics are checked separately. All four dependency arrays and the create/serialize
event DAG are checked; new script/property references are appended to required dependencies.

Six negative variants require specific diagnostics: bad jump, bad context skip, missing function import, missing variable,
wrong English continuation, and an unrelated function mutation. Exact schema comparison supplies another independent
guard; passing parsing alone is insufficient. Evidence is in `independent_validation.json` and `stage2_verification.json`.

## Verification and exact boundary

- .NET8 Release build: 0 warnings/errors; no new dependency installation.
- Two source constructions and explicit reread/resave: both .uasset/.uexp pairs byte-identical.
- Untouched-function raw script and full payload SHA256: 19/19 identical.
- Emitted helper evaluator vs imported canonical segment_units.py: 96 fixtures, including 200-token overflow,
  marks, NBSP/joiners, markup characters, CR/newline, leading gaps, long speakers and non-BMP input.
- Exact threshold domain: 39 cases, both Border colours and both RequestRender calls checked.
- The project verifier includes the new Stage-2 test; final aggregate evidence is `reports/STATIC_VERIFICATION.json`
  and the supervisor's `lastnews/report_010.md`.

The evaluator consumes the re-read generated instructions; it does not execute Unreal. No renderer/runtime result is
inferred from these tests. Timer, per-unit ready-time ledger, Arabic Step/Finish, pause-compatible scheduling,
next-layout-tick capture and live outline/size/wrap extensions are not generated. In this subset, only the initial
speaker threshold is requested; there is no complete playable Arabic reveal or finish/pool handoff yet.

Next smallest implementation: the Arabic Step scheduler with the original Animate While Paused semantics, followed
by the idempotent finish path. This round ends at the clean validated initialization boundary authorized by the task.

## Safety

GAME_NOT_RUN; STEAM_NOT_RUN; PACKAGE_NOT_INSTALLED; original game files unchanged; AES not exposed.
DISPATCH_INTEGRATION_PROVEN=false; IN_GAME_RTL_PROVEN=false; tested_in_game=0; final=0.
ENTIRE_WBP_BYTECODE_UNCHANGED=false (two intentional function changes).
UNTOUCHED_FUNCTION_BYTECODE_UNCHANGED=true. ENGLISH_RUNTIME_BEHAVIOUR_PROVEN is not claimed.

Final aggregate verification: **STATIC_PASS 26/26** (`python -X utf8 scripts/verify_project.py`). Stage1 immutable-file check: 62/62 unchanged.
