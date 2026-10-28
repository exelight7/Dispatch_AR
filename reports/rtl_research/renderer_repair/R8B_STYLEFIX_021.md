# R8b style-table fix (round 021)

Result: **`R8B_STYLEFIX_READY`** (offline; staging pak not installed; game not run).

## Problem (round 020, not re-investigated)

The four DT_AR tables were cloned in round 009 from `DT_SubtitlesProtoRichText`, so they kept RowStruct
`/Script/ProtoAnimatedText.ProtoRichTextStyleRow`. That struct and `/Script/UMG.RichTextStyleRow` are siblings under
`FTableRowBase` (EXE UHT `FStructParams`). Stock `URichTextBlock::RebuildStyleInstance` (EXE `0x1ec95e0`) reads rows only when
`TextStyleSet->RowStruct` IsChildOf `FRichTextStyleRow`. Otherwise it skips them all, so the Arabic RichTexts had no `Default`
row, no `u0..u36` rows, no font and no `M_SubtitlePrinting`. Evidence: `run5_020/style_gate_020.json`.

## Repair: the four tables only

Generator: `asset_inspector --arabic-stylefix-021 <root> <new dir>` (`tools/asset_inspector/ArabicStyleFix021.cs`).
Input: the hash-gated round-019 tables in `builds/rtl_poc/stage1/Dispatch/Content/ArabicReveal/`. These are the Run 5 payload.

For each table:
1. The RowStruct import pair is renamed **in place**:
   - `ProtoRichTextStyleRow` becomes `RichTextStyleRow`;
   - its outer package `/Script/ProtoAnimatedText` becomes `/Script/UMG`.
   Import and NameMap indices do not move.
2. In every row, the eight Proto-only fields are dropped:
   - `PrintLetterAnimationTime`, `PrintLetterInterval`, `UseAdvancedPrintIntervals`;
   - `CommaInterval`, `SentenceInterval`, `EllipsisInterval`;
   - `MidWordDashInterval`, `SpaceInterval`.
   `TextStyle` (FTextBlockStyle, the only field of FRichTextStyleRow) is kept unchanged.
3. Nothing else changes.
   - The package GUID, every other import and the export dependencies are unchanged.
   - Unused NameMap entries also stay, as in round 009, which already left template row names behind.

| Table | RowStruct round 019 | RowStruct round 021 | uasset / uexp (021) |
|---|---|---|---|
| DT_AR_Fill | ProtoAnimatedText.ProtoRichTextStyleRow | **UMG.RichTextStyleRow** | `ee1b723d…f665` / `caa039c4…80af` |
| DT_AR_Fill_Large | same | **UMG.RichTextStyleRow** | `0ac7c57a…d927` / `8182df2e…6262` |
| DT_AR_Outline | same | **UMG.RichTextStyleRow** | `d81c10af…ab10` / `427e3a49…0ce6` |
| DT_AR_Outline_Large | same | **UMG.RichTextStyleRow** | `ce61830b…1b60` / `93620a8f…2801` |

Output: `builds/rtl_poc/r8b_stylefix_021/` (NOT_INSTALLED).

## TextStyle preservation

Two independent proofs, 152/152 rows (4 tables × 38 rows, `Default` and `u0..u36`):

- **Model level** (`textstyle_comparison.json`, C#). For every row, the old and new `TextStyle` property trees are deep-equal.
  - Imports are identical apart from the renamed RowStruct pair, so equal import indices mean equal objects.
  - Field-by-field leaves with object references resolved to paths are also equal: 62 leaves per row.
  - Covered: `Montserrat-Variable` / `Medium`, size 28 or 36, colour, shadow offset and colour, outline settings, the brushes, and the materials:
    - `FontMaterial` is `M_SubtitlePrinting` in all four tables;
    - `OutlineMaterial` is `MI_SubtitlePrinting_Bold` in the outline tables and null in the fill tables.
  - The unit colour encoding is checked: B = 10.5^-unit, plus the outline colour in the outline tables.
- **Byte level** (`textstyle_bytes_021.json`, `tools/r8b_021/textstyle_bytes_021.py`, no UAssetAPI). It parses the UE4.27 header and the DataTable export.
  - Every round-021 row holds exactly one tag, `TextStyle`, byte-identical to the round-019 `TextStyle` tag.
  - **The round-021 export equals the round-019 export with the eight Proto tags cut out, byte for byte.**
  - The ImportMap bytes are identical.
  - The NameMap differs only by the two renames.
  - Run on the round-019 tables, the same script reports FAIL.

## RichTextStyleGate (permanent rule)

`RichTextStyleGate` in `ArabicStyleFix021.cs`, run by `--arabic-stylefix-021` and `--validate-arabic-stylefix-021`.

**Scope.** It finds every DataTable bound to a stock `/Script/UMG.RichTextBlock`:
- **widget defaults:** every export of class `/Script/UMG.RichTextBlock` with a `TextStyleSet`;
- **calls:** every `RichTextBlock.SetTextStyleSet` call inside an `EX_Context`.
  - The target widget class is resolved through the BPGC property.
  - The argument values are resolved through `EX_ObjectConst`, CDO defaults of instance variables, and every `Let`/`LetObj` into a local.
  - A parameter or out-parameter local is unresolved.

**Rule.** Each bound table must have a RowStruct that IsChildOf `/Script/UMG.RichTextStyleRow`. The struct parents come from the EXE evidence.

**Fail-closed cases:**
- an unresolved table;
- a missing RowStruct, or one that is not an import or not a native ScriptStruct;
- an unknown struct;
- a sibling struct;
- `TableRowBase` only;
- an unresolved target or argument;
- a `SetTextStyleSet` call outside a widget context.

Shipped `ProtoRichTextBlock` targets (`ChangeTextToLarge:2/3`) are listed as `EXEMPT_PROTO_WIDGET`: they draw from `ProtoTextStyleSet`.

**Results** (`rowstruct_audit.json`):
- round-019 WBP plus round-021 tables: **14 bindings**, all `CHILD_OF_RichTextStyleRow`:
  - the 2 widget defaults;
  - Set Displayed Line:30 (4 tables through `ARForegroundStyle`), :32 and :34;
  - Arabic Apply Style:11 (4 tables), :13 and :15.
- Same WBP plus the **Run 5 tables: 14/14 rejected**, `SIBLING_NOT_CHILD`.

Negative fixtures: 16, all as expected.
- **Table-side fixtures:**
  - the Run 5 tables;
  - a ProtoRichTextStyleRow table;
  - a TableRowBase table;
  - an unknown native struct;
  - two custom clones (a user struct, and a RichTextStyleRow in another module);
  - a missing RowStruct;
  - a RowStruct that is an export index;
  - a missing table package;
  - one bad table behind the local variable.
- **WBP-side fixtures:**
  - a widget default bound to the shipped Proto table;
  - a constant Proto table argument;
  - a local assigned a Proto table;
  - an unresolved argument;
  - an unresolved target.
- **Accepted:** the correct round-021 tables.

## Unchanged

- The WBP is the round-019 repair, byte-identical (`e4189ec2…6f52` / `9ab47d95…b0b4`). It is not rebuilt. The round-019 validator passes again:
  - return contract: 1120 sites;
  - clock validator;
  - 27 negatives.
- Unchanged reveal design:
  - SetText once, final layout first;
  - word-unit threshold reveal;
  - no substring replacement, no reveal-time shaping, no Reverse(), no Presentation Forms.
- Texts, Fonts and translations are untouched.

## Staging pak

`builds/rtl_poc/r8b_runtime_staging_021/Dispatch_AR_R8b_P.pak`, sha256 `a3402118a351a09b4ae544493f437203c28ce2df8081d24aad729faf3321e916`, 617,744 B.
- Builder: `tools/r8b_021/build_r8b_pak_021.py`. Same workflow as round 019: repak 0.2.3, V11, mount `../../../`, seed 0, uncompressed.
- 10 files: the WBP pair, identical to the 019 pak, plus 8 DT_AR files.
- Built twice, byte-equal. Both unpacked trees are hash-equal to the sources, with no extra files.
- Run 6 procedure: `RUN6_READY.md` in the same folder.

## Not proven

Everything at runtime. With the rows accepted, the next unknowns are:
- the 4.27 font-material vertex-colour threshold (`M_SubtitlePrinting` through FSlateTextRun);
- the `K2_SetTimer` clock;
- widget binding;
- RetainerBox shadow capture;
- the RTL reveal itself.
