# Translation / UI backlog (round 019)

Source: the Run 4 operator observations as relayed by the supervisor in `supervisor_reply_019.md`. Run 4 was Texts + Fonts +
`-culture=ar`, with no R8b and no Locmeta. **No screenshot files are stored in the project.** Each entry therefore needs the
screen, the string key and a screenshot before anyone acts on it. Hypotheses are labelled as such and are unverified.

No translation data was edited in round 019. The renderer (R8b Run 5) comes first. Every item below is `OPEN` and deferred.

| ID | Category | Where | Observed (relayed) | Working hypothesis (unverified) | Needed before work starts |
|---|---|---|---|---|---|
| B01 | SUBTITLE_READABILITY | Gameplay subtitles (stock Proto) | Reveal runs left to right, does not start from the right, glyphs overlap or interleave while appearing, and the layout looks unstable during the reveal | Known root cause: Proto paints per UTF-16 slice with a logical left-to-right pen (`PAINT_MODEL_LOGICAL_PEN`, round 002). **Not a translation issue.** | Run 5 with the repaired R8b (this round). Stock Proto stays rejected. |
| B02 | TEXT_OVERLAP | Menu and settings | Some labels overlap controls | Arabic strings are longer than the English ones in fixed-width boxes, and/or Naskh ascent (1.07 em) is taller than Montserrat | Per screen: string key, widget and screenshot |
| B03 | UI_ALIGNMENT | Mixed UI text | Some alignment problems | LTR-authored widgets keep Left justification under `ar` | Screenshot plus widget name, then decide per widget, never globally |
| B04 | MIXED_BIDI | Strings mixing Arabic, digits and punctuation | Placement of digits and punctuation can look wrong | Neutral characters resolve against an LTR base direction at string edges. The project bans bidi control characters in data (Unicode safety: 0 controls), so a fix must not insert RLM/ALM blindly. | List of exact strings and keys, observed versus expected order |
| B05 | WORDING_CONTEXT | Subtitles and UI | Some wording and context needs review | Includes the 18 records flagged "needs in-game context" in the round-006 review. Speaker and addressee gender is a known risk area. | String keys from the operator. Review only those, no mass edit. |
| B06 | FONT_METRICS | All Arabic text (Naskh fallback) | Possible clipping and weight mismatch (supervisor note) | As predicted in report 017: Naskh Regular sits beside Montserrat Medium, tashkeel may clip, and there is no Arabic italic | Close-up screenshots of a subtitle line with harakat and of a dense button |
| B07 | SUBTITLE_READABILITY | Long subtitles under R8b | (not yet observable) | R8b caps lines at 37 reveal units and merges the tail. This affects 20 corpus lines (round 008). | Run 5 test T14 |

Ordering for later rounds: B01 (Run 5) → B06 → B02/B03 (screens) → B04 → B05. None of these blocks the R8b repair.
