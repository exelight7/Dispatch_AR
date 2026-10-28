# NEEDS_CONTEXT review (round 008, static adjacency only)

There are 18 records with status `TRANSLATED` (= NEEDS_CONTEXT in `FINAL_VERIFICATION.json`). Their `notes` fields are empty, so every "reason" below is this round's reading and is marked as such. **No translation data was changed.**

## Resolvable from static evidence (9): proposed for human sign-off, not marked REVIEWED

The `ScenarioBulletPoints(0..4)` of two shift scenarios spell a single sentence in index order:

| Scenario | Index order (EN) | Index order (AR) | Status of siblings |
|---|---|---|---|
| `LV_Shift08b … SC_SonarConvoy_3` | Give / Him / Everything / You've / Got | أعطِ / إياه / كل / ما / لديك | all 5 TRANSLATED |
| `LV_Shift08c … SC_CoupeConvoy_3_Max` | Give / Her / Everything / You've / Got | أعطِ / إياها / كل / ما / لديك | 4 TRANSLATED; `• Her → • إياها` already REVIEWED |

Read top to bottom, the Arabic is «أعطِ إياه/إياها كل ما لديك» ("give him/her everything you have"). It is grammatical and uses the English word order slot for slot, so each bullet stays correct as a fragment. The already-reviewed sibling confirms the scheme. Verdict: **RESOLVED_BY_STATIC_EVIDENCE (pending sign-off)**.

## KEEP_NEEDS_CONTEXT (9)

| Id | EN → AR | Speaker | Reason (this round's reading) |
|---|---|---|---|
| 101:Line:AD7E5926… | "…Which I guess I don't have to worry about" → «وأظن أنني لم أعد مضطرا للقلق من هذا» | Robert | "لم أعد" adds "anymore"; depends on scene |
| 101:NodeTitle:47799029… | It was all for you. → كان كله من أجلكم. | choice | addressee number/gender (plural chosen) |
| 103:NodeTitle:1ABAC2DD… | No, I don't. → لا، لا أفعل. | choice | depends on the question asked |
| 105:Line:490541F5… | You decent? → هل أنت محتشمة؟ | Blonde Blazer | addressee gender assumed female |
| 107:NodeTitle:38C0F1C3… | Yeah, I think he did. → أجل، أظنه فعل الصواب. | choice | "the right thing" is interpretive |
| 108:Line:055F5062… | Being a professional yourself… → بما أنك محترف أيضًا… | Robert | addressee gender (masculine chosen) |
| 108:NodeTitle:27F36DEE… | Come after me. → تعال ورائي. | choice | "follow me" vs "attack me" |
| Shared::20EAD6A1… | Welcome to SDN's ^Dispatcher^ → مرحبًا بك في ^منسق العمليات^ لدى SDN | tutorial | the glossary term is a person role; the line may name the software (sibling: "^SDN's Hero Database^") |
| Shared:ExtrasStrings:ComicTitle_TheLastBender | The Last Bender → المسخّر الأخير | menu | title pun / official naming unknown |

The prev/next records in `translation/records/*.json` are ordered by key, not by dialogue. Real dialogue adjacency therefore needs the story-node graph, which was not re-extracted (out of scope this round).
