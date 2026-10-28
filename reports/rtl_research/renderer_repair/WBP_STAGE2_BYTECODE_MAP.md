# R8b WBP Stage-2 bytecode map — prepared, NOT EXECUTED

> **Round 010 update:** the initialization subset of this historical map is now generated and validated on a detached
> copy: export11 language split, Arabic helpers/initialization, and export12 cleanup. See `WBP_STAGE2_RESULT.md` and
> `builds/rtl_poc/stage2/`. Timer/Arabic Step/Finish and live style/wrap extensions below remain planned, not emitted.
> The Stage-1 source and its original instruction inventory remain unchanged.

2026-10-25. Stage 1 is `R8B_WBP_STAGE1_PASS` for offline structure only. The original 21 functions remain byte-identical.
Source: `builds/rtl_poc/stage1/original_wbp_baseline.json`; offsets and SHA256:
`builds/rtl_poc/stage1/stage2_instruction_inventory.json`. All instruction indices below are **zero-based**;
exports are **one-based**. Logical offsets come from UAssetAPI `ExpressionSerializer.WriteExpression`'s VM-size return,
not the stream position. The inventory separately records serialized offsets/sizes. New addresses must be generated
from labels after serialization; none of the numbers below may be used as a guessed patched address.

## 1. Exact language seam and Set Displayed Line (export 11)

| Original instructions | Logical offsets | Existing operation | Stage-2 intent |
|---|---|---|---|
| 0, 1 | 0, 5 | PushExecutionFlow: return 1238, invalidate-layout 1100 | Scope both pushes to the English branch; do not enter Arabic with these pending continuations |
| 2 | 10 | SubtitleOverlay.SetVisibility | Preserve shared side effect |
| 3–5 | 48–121 | SubtitleColor conversion/assignment; Update Text Color | Preserve shared order and values |
| 6 | 135 | Dispatch Filter Text Profanity -> local Potentially_Censored_Text | Shared, once; insert language seam immediately **after** this expression (next old offset 199) |
| 7–9 | 199, 222, 268 | Bind Format As Subtitle Text With Tags; ProcessLocalizedTextWithCallback; Apply Speaker Name if Needed | English-only original instructions/parameters; Arabic uses a separate plain-text callback |
| 10–11 | 318, 363 | Proto SetText twice | English-only original text, targets and order |
| 12–22 | 408–836 | Letterbox setting reads, visibility, opacity | Preserve for English; Arabic helper reproduces these same shared setting side effects once |
| 23–25 | 877–949 | Typewriter setting reads | English unchanged; Arabic reads the same setting |
| 26 | 1013 | JumpIfNot -> 1165 | Relocate to old instruction 33's new label |
| 27–29 | 1027,1063,1099 | PrintLetterByLetter twice, PopExecutionFlow | English only; original flow stack preserved |
| 30–32 | 1100,1132,1164 | InvalidateLayoutAndVolatility twice, PopExecutionFlow | English continuation; old push 1 must target relocated instruction 30 |
| 33–35 | 1165,1201,1237 | ShowText twice, PopExecutionFlow | English only; same delegate/finish route |
| 36–37 | 1238,1240 | Return, EndOfScript | Common return label; old push 0 targets relocated instruction 36 |

Planned CFG (no implementation emitted):

```text
shared original side effects [old 2..6]
L = GetCurrentLanguage()
bArabic = (L == "ar") OR StartsWith(L, "ar-")
if !bArabic:
    Arabic cleanup/collapse only if this block previously served Arabic
    restore original English widget visibilities (pool reuse)
    [old pushes 0,1; old 7..37 with labels relocated]
else:
    Begin Arabic Line(Potentially_Censored_Text, SubtitleDisplayInfo)
    goto common Return             # no English execution-flow pushes pending
```

The pushes are control bookkeeping, with no outward side effect; moving them behind the language seam preserves
the English side-effect order and its two continuation targets. Stage-2 must prove this with a CFG/flow-stack model,
including typewriter true/false and null context skips. Do not blindly insert an Arabic return into the old pushed flow.
Changing this function necessarily changes its bytecode: preservation in Stage 2 means the original English
instructions/operands and observable flow, allowing only explicitly verified address relocation. Stage-1 byte equality
is a stronger, different assertion and must not be relabelled as an English runtime test.

`L="arn"` and `L="en"` must go English; `ar` and `ar-SA` go Arabic. No character detection and no raw StartsWith("ar").

## 2. Other exact mutation sites

| Export/function | Current instruction/offset | Planned addition and preservation rule |
|---|---|---|
| 12 Stop Displaying Line | 0@0 SetVisibility; 1@38 Return | Before Return: clear/invalidate Arabic timer, mark inactive, Set Threshold Arabic(-1), collapse all Arabic widgets; no finish broadcast on cancellation. Preserve original visibility call |
| 14 Set Has Outline | 0@0 Has Outline assignment; 1@19 !Has Outline; 2@48 and 3@89 SetRetainRendering; 7@189 shadow visibility; 8@278 Return | Keep the original block. Before Return, when Arabic active, select Outline/Fill and matching Large foreground table; shadow always Fill/Fill_Large; mirror retain/visibility state. Table changes only at initialization/style transition, never each reveal step |
| 19 ChangeTextToLarge | 0@0,1@45 SetProtoTextStyleSet; 2@90,3@131 SetTextStyleSet; 4@172,5@204 invalidation; 6@236 Return | Original operations remain English. Arabic branch sets size state and chooses from the four handles; RequestRender H/V once after layout. Do not send Proto style calls to stock RichTextBlock |
| 21 Set Wrap Text At | 0@0 Wrap Text Length assignment; 1@27,2@55 AdHocUtils.SetTextWrapAt; 3@83 Return | Retain assignment. English calls preserved; Arabic uses the **stock** text layout setter/property for both RichTextBlocks, preserving 1050 initial width/center justification. Do not pass stock widgets to a Proto-only utility |
| 2 ExecuteUbergraph | 23@728,24@760 RequestRender; 41@1295 finish delegate; 43@1328 PreConstruct; 44@1347,45@1375 SetTextWrapAt | English event bodies stay unchanged. Arabic Step handles Arabic retainers itself. Arabic Finish invokes the existing finish delegate signature exactly once. Arabic wrap initialization supplements the PreConstruct path |
| 2 ExecuteUbergraph | 4@97 parent OnInitialized; 5@107 Setup Dynamic Material; 6@121 and 7@144 delegate bind/add; 20@659 and 21@682 bind/add | Keep original English initialization/delegate bindings. Add only language-neutral safe Arabic reference initialization; no timer starts here |
| 15 Update Text Color | 5@203 SetVectorParameterValue; 6@301 Return | Existing MID update unchanged. R8b foreground is white; do not feed subtitle RGB into ancestor tints. Optional colourize route remains unproven and outside this patch |
| 18 Setup Dynamic Material | 0@0 CreateDynamicMaterialInstance; 1@45 assign Font Material Instance; 2@64 OverrideFontMaterial; 3@105 Return | English material setup unchanged. R8b requires no new font MIDs/materials/shaders |
| 13 Format As Subtitle Text With Tags / 16 Apply Speaker Name if Needed / 17 Get Text Tag Opener | Entire functions | Preserve as English helpers. Arabic must not reuse their Proto tags |
| 3 PreConstruct / 4 finish callback / 5 colour callback / 6–7 letterbox callbacks / 8 On Print Letter / 9 OnInitialized / 10 Construct | Thin entries into export 2 | Preserve entry-point operands, or relocate every affected entry-point literal if the Ubergraph changes |
| 20 WBP_SubtitleBlock_AutoGenFunc | Entire function | No planned change |

The previous line's bArabic value is unsafe for `ChangeTextToLarge`/outline/wrap calls issued before Set Displayed Line.
Stage 2 must retain style/size/wrap state independently, apply it at Arabic initialization, and avoid relayout during reveal.
All seven widgets are Collapsed in Stage 1: Stage 2 must explicitly enable the root **and** the required descendants,
and respect the outline/shadow mode. Showing only ArabicRoot will display nothing.

## 3. Planned helpers (new functions, no bodies emitted in Stage 1)

| Helper | Input -> output | State/side effects | Idempotence |
|---|---|---|---|
| Format As Arabic Plain | callback text -> text, same delegate signature as the game's processor | Remove exactly `<Italic>` and `</>`; no speaker tags, no segmentation yet | Pure; repeated stripping stable |
| Build Arabic Markup | final processed plain content, optional plain speaker, capacity=37 -> markup, count, speakerCount, delays | Exact canonical `segment_units.py` policy, escaped markup; segment once before SetText | Pure for identical inputs |
| Set Threshold Arabic | integer t -> none | Write both Borders (1,1,t<0 ? 0 : 10.5^min(t,36),1); request H/V render; never SetText or table | Same threshold gives same visual state; refresh allowed |
| Arabic Step | timer callback -> none | Ignore inactive/finished block; reveal next unit at its ready time; arm one-shot next delay; on last call Finish | Repeated callback before next ready time must not advance early |
| Arabic Finish | active line -> none | Finished guard first; clear/invalidate timer; threshold=count-1 (empty text stays -1); broadcast existing finish once | Required: repeated skip/finish never double-broadcast |
| Begin Arabic Line | censored text, speaker/display settings -> none | Clear old timer first, inactive/reset guard; run plain callback; build once; select tables/wrap; threshold -1 **before** SetText x2; collapse/clear Proto; enable Arabic; render now and after next layout tick; speaker visible immediately; start timer or Finish | Resets all per-block state on every line |
| Cancel Arabic Line | none -> none | Clear/invalidate timer, inactive; hide threshold/layer; no finish broadcast | Safe repeated cancellation |

New BPGC fields planned: `bArabic`, `bArabicActive`, `bArabicFinished`, `bArabicLarge`, `ArabicThreshold`,
`ArabicUnitCount`, `ArabicSpeakerUnits`, `ArabicUnitDelays` (float array), `ArabicNextReadyTime`, `ArabicTimer`
(TimerHandle), and pending post-layout render state. Named widget/table handles already exist from Stage 1.
No native offsets are guessed: FFieldPath resolves by name/owner. New function locals must be typed FProperties with
CPF_Parm/OutParm/ReturnParm only where appropriate; temporary values are function locals, not arbitrary UberGraphFrame offsets.

Timer API plan: stock KismetSystemLibrary delegate timer/clear APIs, one shot per next delay; stock Border tint and
RetainerBox.RequestRender calls. Exact import signatures/property owners must be resolved before emission. A cleared
old callback must not affect a reused block: inactive/finished and next-ready-time checks are required. Pause semantics
(`Animate While Paused`), first post-SetText capture scheduling, delegate timing and skip races are **not proven**;
Stage 2 must choose a clock/dispatch path matching the original paused behaviour before claiming timing compatibility.

## 4. Canonical segmentation contract

Reuse `tools/ue427_stock_reveal_test/segment_units.py`; do not fork or rewrite its rules. The Stage-1 integration test imports
this module and sets its configurable module capacity to 37 for the R8b fixtures.

- Split only U+0020/U+0009/U+000A/U+000D. NBSP, narrow NBSP, ZWSP, ZWJ, ZWNJ, harakat and tatweel do not split.
- Letterless tokens attach to the previous unit with the intervening gap, except with a newline/no predecessor;
  preserve the reference implementation's exact newline predicate and test it before porting.
- Plain speaker prefix follows the existing speaker setting and nonempty-name condition. Speaker units are immediately visible.
- Units 36..end merge into unit 36 at overflow. Preserve all characters, gaps and accumulated delay; no truncation.
- Escape `&`, `<`, `>`, and `"`; unescaping emitted markup must reconstruct the final plain line.
- Timing must follow the actual `letters()` reference routine: nonseparator, noncombining characters contribute,
  including digits/punctuation. Do not silently substitute a Unicode-letter-only rule based on its name.
- Retain an event/time ledger before tail merging. The final merged unit consumes every tail delay rather than
  dropping timing events. The current reference coalesces the tail into one delay; tests prove its total is conserved.

The reference's leading-content-whitespace handling when a speaker is present, CR-only letterless-token gaps,
and speaker names exceeding capacity require explicit Stage-2 fixtures; no claim is made that these edge cases have
been ported correctly. Do not change the canonical policy silently. The ordinary 37-unit overflow/markup/timing fixtures pass.

## 5. Relocation and acceptance gates for the next generator

Maintain a label for **every original instruction and branch destination**, plus new labels. Recompute recursively:
`CodeOffset`, `PushingAddress`, `EndGotoOffset`, switch `NextOffset`, `EX_Context.Offset` skip lengths, and all nested
`SkipOffset`/execution-flow operands found in the parsed tree. Do not add a constant delta to all addresses: the seam
and English-only pushes relocate different regions by different amounts.

For export 11 specifically: old 0->1238, old 1->1100 and old 26->1165 are mandatory label relocations. Context skips
inside instructions 2,6,10,11,18,22,27,28,30,31,33,34 must be recomputed if their expression bodies change. Nested
switch targets inside old 18 and export-14 instruction 7 also need relocation. If export 2 changes, its computed-jump
entry labels and literals passed by all thin event-entry functions must remain paired.

Stage-2 acceptance must compare the English CFG/opcodes/target objects/parameters, not demand the old entire
modified function's hash. Keep Stage-1 baseline/raw script hashes, verify new imports/FFieldPaths/local schemas,
check every destination is an expression boundary (or valid nested expression endpoint), simulate both flow-stack
paths, and negative-test bad jumps, duplicate finish, stale pooled callbacks, incorrect language `arn`, empty text,
speaker-only text, disabled typewriter and outline/size transitions. No Stage-2 mutation is authorized by this map.

The accompanying instruction inventory gives every current root instruction's logical/serialized span. The original
typed JSON supplies every nested address operand; the generated appendix below lists the current relocation operands
in the functions that are expected to change.

## 6. Current relocation operand inventory (generated from original typed JSON)

Full machine-readable paths: `builds/rtl_poc/stage1/stage2_relocation_inventory.json`. `Offset` is a context skip length; the other listed operands are logical VM destinations. These are original values only.

| Export | Instruction @ logical offset | Operand path | Current value |
|---|---|---|---|
| 2 | 1 @ 10 | `ScriptBytecode[1].VariableExpression.Offset` | 9 |
| 2 | 2 @ 51 | `ScriptBytecode[2].VariableExpression.Offset` | 9 |
| 2 | 3 @ 92 | `ScriptBytecode[3].CodeOffset` | 1403 |
| 2 | 7 @ 144 | `ScriptBytecode[7].Delegate.Offset` | 9 |
| 2 | 9 @ 215 | `ScriptBytecode[9].AssignmentExpression.Offset` | 10 |
| 2 | 11 @ 280 | `ScriptBytecode[11].Delegate.ObjectExpression.Offset` | 9 |
| 2 | 11 @ 280 | `ScriptBytecode[11].Delegate.Offset` | 9 |
| 2 | 13 @ 373 | `ScriptBytecode[13].AssignmentExpression.Offset` | 10 |
| 2 | 15 @ 438 | `ScriptBytecode[15].Delegate.ObjectExpression.Offset` | 9 |
| 2 | 15 @ 438 | `ScriptBytecode[15].Delegate.Offset` | 9 |
| 2 | 17 @ 531 | `ScriptBytecode[17].AssignmentExpression.Offset` | 10 |
| 2 | 19 @ 596 | `ScriptBytecode[19].Delegate.ObjectExpression.Offset` | 9 |
| 2 | 19 @ 596 | `ScriptBytecode[19].Delegate.Offset` | 9 |
| 2 | 21 @ 682 | `ScriptBytecode[21].Delegate.Offset` | 9 |
| 2 | 22 @ 723 | `ScriptBytecode[22].CodeOffset` | 1403 |
| 2 | 23 @ 728 | `ScriptBytecode[23].Offset` | 10 |
| 2 | 24 @ 760 | `ScriptBytecode[24].Offset` | 10 |
| 2 | 25 @ 792 | `ScriptBytecode[25].CodeOffset` | 1403 |
| 2 | 27 @ 827 | `ScriptBytecode[27].AssignmentExpression.Offset` | 10 |
| 2 | 28 @ 869 | `ScriptBytecode[28].AssignmentExpression.ObjectExpression.Offset` | 9 |
| 2 | 28 @ 869 | `ScriptBytecode[28].AssignmentExpression.Offset` | 10 |
| 2 | 32 @ 992 | `ScriptBytecode[32].Offset` | 67 |
| 2 | 32 @ 992 | `ScriptBytecode[32].ContextExpression.Parameters[0].EndGotoOffset` | 1080 |
| 2 | 32 @ 992 | `ScriptBytecode[32].ContextExpression.Parameters[0].Cases[0].NextOffset` | 1057 |
| 2 | 32 @ 992 | `ScriptBytecode[32].ContextExpression.Parameters[0].Cases[1].NextOffset` | 1071 |
| 2 | 34 @ 1111 | `ScriptBytecode[34].AssignmentExpression.Offset` | 10 |
| 2 | 35 @ 1153 | `ScriptBytecode[35].Expression.ObjectExpression.Offset` | 9 |
| 2 | 35 @ 1153 | `ScriptBytecode[35].Expression.Offset` | 10 |
| 2 | 36 @ 1225 | `ScriptBytecode[36].Offset` | 19 |
| 2 | 37 @ 1266 | `ScriptBytecode[37].CodeOffset` | 1403 |
| 2 | 38 @ 1271 | `ScriptBytecode[38].CodeOffset` | 797 |
| 2 | 40 @ 1290 | `ScriptBytecode[40].CodeOffset` | 1403 |
| 2 | 42 @ 1323 | `ScriptBytecode[42].CodeOffset` | 1403 |
| 11 | 0 @ 0 | `ScriptBytecode[0].PushingAddress` | 1238 |
| 11 | 1 @ 5 | `ScriptBytecode[1].PushingAddress` | 1100 |
| 11 | 2 @ 10 | `ScriptBytecode[2].Offset` | 16 |
| 11 | 6 @ 135 | `ScriptBytecode[6].Offset` | 42 |
| 11 | 10 @ 318 | `ScriptBytecode[10].Offset` | 23 |
| 11 | 11 @ 363 | `ScriptBytecode[11].Offset` | 23 |
| 11 | 13 @ 438 | `ScriptBytecode[13].AssignmentExpression.Offset` | 10 |
| 11 | 14 @ 480 | `ScriptBytecode[14].AssignmentExpression.ObjectExpression.Offset` | 9 |
| 11 | 14 @ 480 | `ScriptBytecode[14].AssignmentExpression.Offset` | 10 |
| 11 | 18 @ 603 | `ScriptBytecode[18].Offset` | 67 |
| 11 | 18 @ 603 | `ScriptBytecode[18].ContextExpression.Parameters[0].EndGotoOffset` | 691 |
| 11 | 18 @ 603 | `ScriptBytecode[18].ContextExpression.Parameters[0].Cases[0].NextOffset` | 668 |
| 11 | 18 @ 603 | `ScriptBytecode[18].ContextExpression.Parameters[0].Cases[1].NextOffset` | 682 |
| 11 | 20 @ 722 | `ScriptBytecode[20].AssignmentExpression.Offset` | 10 |
| 11 | 21 @ 764 | `ScriptBytecode[21].Expression.ObjectExpression.Offset` | 9 |
| 11 | 21 @ 764 | `ScriptBytecode[21].Expression.Offset` | 10 |
| 11 | 22 @ 836 | `ScriptBytecode[22].Offset` | 19 |
| 11 | 24 @ 907 | `ScriptBytecode[24].AssignmentExpression.Offset` | 10 |
| 11 | 25 @ 949 | `ScriptBytecode[25].AssignmentExpression.ObjectExpression.Offset` | 9 |
| 11 | 25 @ 949 | `ScriptBytecode[25].AssignmentExpression.Offset` | 10 |
| 11 | 26 @ 1013 | `ScriptBytecode[26].CodeOffset` | 1165 |
| 11 | 27 @ 1027 | `ScriptBytecode[27].Offset` | 14 |
| 11 | 28 @ 1063 | `ScriptBytecode[28].Offset` | 14 |
| 11 | 30 @ 1100 | `ScriptBytecode[30].Offset` | 10 |
| 11 | 31 @ 1132 | `ScriptBytecode[31].Offset` | 10 |
| 11 | 33 @ 1165 | `ScriptBytecode[33].Offset` | 14 |
| 11 | 34 @ 1201 | `ScriptBytecode[34].Offset` | 14 |
| 12 | 0 @ 0 | `ScriptBytecode[0].Offset` | 16 |
| 14 | 2 @ 48 | `ScriptBytecode[2].Offset` | 19 |
| 14 | 3 @ 89 | `ScriptBytecode[3].Offset` | 19 |
| 14 | 7 @ 189 | `ScriptBytecode[7].Offset` | 67 |
| 14 | 7 @ 189 | `ScriptBytecode[7].ContextExpression.Parameters[0].EndGotoOffset` | 277 |
| 14 | 7 @ 189 | `ScriptBytecode[7].ContextExpression.Parameters[0].Cases[0].NextOffset` | 254 |
| 14 | 7 @ 189 | `ScriptBytecode[7].ContextExpression.Parameters[0].Cases[1].NextOffset` | 268 |
| 15 | 1 @ 30 | `ScriptBytecode[1].AssignmentExpression.Offset` | 10 |
| 15 | 3 @ 120 | `ScriptBytecode[3].AssignmentExpression.ObjectExpression.Offset` | 9 |
| 15 | 3 @ 120 | `ScriptBytecode[3].AssignmentExpression.Offset` | 10 |
| 15 | 5 @ 203 | `ScriptBytecode[5].Offset` | 76 |
| 15 | 5 @ 203 | `ScriptBytecode[5].ContextExpression.Parameters[1].EndGotoOffset` | 300 |
| 15 | 5 @ 203 | `ScriptBytecode[5].ContextExpression.Parameters[1].Cases[0].NextOffset` | 277 |
| 15 | 5 @ 203 | `ScriptBytecode[5].ContextExpression.Parameters[1].Cases[1].NextOffset` | 291 |
| 18 | 2 @ 64 | `ScriptBytecode[2].VariableExpression.Offset` | 9 |
| 19 | 0 @ 0 | `ScriptBytecode[0].Offset` | 23 |
| 19 | 1 @ 45 | `ScriptBytecode[1].Offset` | 23 |
| 19 | 2 @ 90 | `ScriptBytecode[2].Offset` | 19 |
| 19 | 3 @ 131 | `ScriptBytecode[3].Offset` | 19 |
| 19 | 4 @ 172 | `ScriptBytecode[4].Offset` | 10 |
| 19 | 5 @ 204 | `ScriptBytecode[5].Offset` | 10 |
