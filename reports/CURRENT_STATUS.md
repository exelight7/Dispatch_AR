# 2026-10-28 — Full dialogue review installed

Read all 8,369 dialogue/choice/VO records; applied52 corrections after independent secondcheck. All465 English settings labels preserved. Structural errors0; QAerrors0, warnings291. Packageaudit9/9; installed SHA256 `1893e962132c9ae832e8fdb0de06389b7d5c34acfd68da08a8ae61c3a3d7953d`. OtherPAKs unchanged. Game not launched; no new visual acceptance. Report: `reports/translation/dialogue_review_20261028.md`.

# الحالة الحالية — Dispatch Arabic

**تحديث الإعدادات — 2026-10-28:** رُكبت حزمة إعدادات إنجليزية مع بقاء الحوارات بالعربية. تغيرت396 تسمية ضمن465 قيمة إعدادات/مفاتيح تحكم، دون تغيير قيم خيارات اللاعب أو لغة التشغيل. SHA256 `6c56b80e26e86f2977cb9a895a8a163114def3d08340bc7f3443d87f0bc106ff`. Fonts/R8b وبقية الحزم محفوظة، لا اختبار تشغيل جديد. التقرير: `reports/translation/settings_english_20261028.md`؛ الإيصال: `backups/settings_english_20261028/installation_receipt.json`.

**تحديث النصوص — 2026-10-27:** رُكبت حزمة النصوص بعد المراجعات اللغوية. SHA256 `88db2b97f376855bfa43d2f9fe400a8b10cc533a104aeb72e26b61a5d6381533`؛ تشمل270 تغييرًا مقارنة بالحزمة السابقة، و36 تصحيحًا من القراءة الثالثة. توقفت القراءة الثالثة بطلب المستخدم عند8079/8369 سجلًا؛ المراجعتان السابقتان كاملتان للنطاق المحدد. حزم Fonts/R8b وبقية ملفات الحزم محفوظة. لا تشغيل للعبة ولا اختبار بصري جديد. التفاصيل: `reports/translation/dialogue_proofread_20261027_pass3_installed.md`؛ والإيصال: `backups/proofread_20261027_pass3/installation_receipt.json`.

**الأحدث: الجولة 022 — 2026-10-26:** `R8B_RUN6_PARTIAL` (شغّل المشغّل اللعبة؛ الجلسة لم تشغّلها).

- **التركيب:** حزمة R8b من الجولة 021 (`a3402118…e916`) مع Texts وFonts و`-culture=ar`، بلا Locmeta. النسخ الاحتياطي والبصمات والإيصال في `backups/runtime_run6_022_20261026_002031_875/`. ما زالت مركّبة.
- **ما رآه المشغّل (6A):** لا انهيار، والترجمة العربية ظاهرة، والكشف يبدأ من اليمين ويتقدم نحو اليسار. لكن الحركة أقل سلاسة بوضوح من الأصل.
- **ما ثبت داخل اللعبة:** `ARABIC_SUBTITLE_VISIBLE` و`RTL_DIRECTION_RUNTIME_PROVEN` و`R8B_THRESHOLD_RUNTIME_PROVEN` و`R8B_CLOCK_RUNTIME_PROVEN` (مسار اللعب AWP=false).
- **ما لم يُرصد صراحة:** ثبات الحروف، والوصل أثناء الكشف، وعلامات الترقيم، وتزامن الظل. لذلك `IN_GAME_RTL_PROVEN=false`.
- **سبب عدم السلاسة (تحليل خارج اللعبة، `run6_022/cadence_022.json`):** الكشف كلمةً كلمة.
  - R8b: ‏8.4 تغيّر مرئي في الثانية، بمتوسط 4.6 حرف لكل تغيّر. Proto: ‏37.2 تغيّر في الثانية، حرف واحد كل مرة.
  - كل كلمة تظهر دفعة واحدة عند موعد آخر حروفها.
  - المؤقت ليس السبب: نهاية السطر تطابق الأصل ضمن إطار واحد، ولا يُكشف أكثر من وحدة في إطار واحد.
- **مشكلة مستقلة:** أسماء خيارات الإعدادات ما زالت مختفية (`SETTINGS_LABELS_MISSING=true`)، ونسبتها إلى R8b غير مثبتة.
- القيم: `final=0`. التقرير: `lastnews/report_022.md`. التفاصيل: `reports/rtl_research/renderer_repair/RUN6_RESULT_022.md`.

**الجولة 021 — 2026-10-25:** `R8B_STYLEFIX_READY` (خارج اللعبة؛ لم تُشغّل اللعبة ولم تُركّب الحزمة الجديدة).

- **التراجع عن Run 5:** نُفّذ `rollback_r8b_run5.ps1`، فأُزيلت حزمة R8b المعطوبة وحدها ونُقلت إلى `backups/runtime_run5_020_20261025_111003_531/rollback/`.
  - بقيت Texts وFonts و`-culture=ar` كما هي، بلا Locmeta، وهي حالة Run 4.
  - الإيصال: `ROLLBACK_RECEIPT_021.json`.
- **الإصلاح:** أُعيد بناء جداول DT_AR الأربعة وحدها بنوع صفوف `/Script/UMG.RichTextStyleRow`، وحُذفت حقول Proto الثمانية.
  - `TextStyle` مطابق بايتًا ببايت في 152/152 صفًا.
  - ملف WBP من الجولة 019 لم يتغير.
  - المخرجات في `builds/rtl_poc/r8b_stylefix_021/`.
- **قاعدة دائمة `RichTextStyleGate`:** كل جدول مربوط بـ RichTextBlock قياسي يجب أن يكون نوع صفوفه فرعًا من `RichTextStyleRow`.
  - تمر على 14 ربطًا.
  - ترفض جداول Run 5 كلها، و16 حالة اختبار سلبية تتصرف كما يُتوقع.
- **الحزمة:** `builds/rtl_poc/r8b_runtime_staging_021/Dispatch_AR_R8b_P.pak` ‏(`a3402118…e916`). حتمية وغير مركّبة.
- **Run 6:** الإجراء في `RUN6_READY.md`: الحركة مفعّلة (6A)، ثم معطّلة عبر `Arabic Finish` ‏(6B).
- القيم: `IN_GAME_RTL_PROVEN=false`، `final=0`. التقرير: `lastnews/report_021.md`.

**الجولة 020 — 2026-10-25:** `R8B_RUN5_FAIL`.

- **التركيب:** Texts + Fonts + R8b المُصلَح (`1058eac4…f988`) + `-culture=ar`، بلا Locmeta. النسخ الاحتياطي والبصمات قبل التشغيل وبعده وإيصال التركيب في `backups/runtime_run5_020_20261025_111003_531/`.
- **ما رآه المشغّل:** اللعبة تعمل، ولا انهيار في المشهد الأول. لكن منطقة الترجمة فارغة تمامًا، وأسماء خيارات كثيرة في الإعدادات مختفية.
- **انهيار الإطار:** أُصلح فعليًا داخل اللعبة (`FRAME_CRASH_FIXED_RUNTIME=true`). اختفاء نص Proto يثبت أن الفرع العربي نُفّذ وتجاوز التعليمة 66 بلا انهيار.
- **سبب الترجمة الفارغة (مثبت من الملف التنفيذي):** جداول DT_AR الأربعة بنوع صفوف `ProtoRichTextStyleRow`، وأصله `FTableRowBase` لا `FRichTextStyleRow`.
  - الدالة `URichTextBlock::RebuildStyleInstance` (‏0x1ec95e0) لا تقرأ الصفوف إلا إذا كان نوعها فرعًا من `FRichTextStyleRow`، فتُهمل الجدول كله.
  - النتيجة: لا صف Default ولا u0..u36، ولا خط ولا مادة، فلا يُرسم أي حرف.
  - الدليل: `reports/rtl_research/renderer_repair/run5_020/style_gate_020.json` والتحليل في `RUN5_FAILURE_020.md`.
- **أسماء الإعدادات:** حزمة R8b لا تصل إلا إلى `WBP_SubtitlesWidget` و`WBP_SubtitlePreview`، فنسبة اختفاء الأسماء إليها غير مثبتة.
- **تغييرات كتبتها اللعبة أثناء التشغيل:** DialogueBoost وMonoAudio وعمى الألوان (Tritanope). اللغة بقيت `system`.
- **ما زال مركّبًا:** R8b مركّبة كما هي، وسكربت إزالتها وحدها `work/rollback_r8b_run5.ps1`.
- القيم: `R8B_SUBTITLE_RENDERING_FAILED=true`، `IN_GAME_RTL_PROVEN=false`، `final=0`. التقرير: `lastnews/report_020.md`.


**الجولة 019 — 2026-10-25:** `R8B_REPAIR_READY` (خارج اللعبة فقط؛ لم يُركّب شيء ولم تُشغّل اللعبة).

- **إصلاح خلل Run 2:** صارت `Build Arabic Timing` دالة void. حُذفت خاصية ReturnValue من نوع FString وعلَم `FUNC_HasOutParms`، واستُبدل `Return Local(Output)` بـ`Return Nothing`.
- **الأرقام:** PropertiesSize ‏216→200، وParmsSize ‏48→32، وReturnValueOffset ‏32→MAX_uint16.
- **لا تغيير في السلوك:** النداء الوحيد (التعليمة 66، جملة مستقلة) لم يكن يستهلك القيمة، وسجل التأخيرات يطابق المرجع على 96 حالة.
- **البناء:** من المصدر النظيف (011 ← الإصلاح ← مولّد 012)، ومطابق بايتياً لتطبيق الإصلاح على زوج 012 المجمّد. حتمي، وإعادة الحفظ مطابقة. 72 من 73 كائنًا مطابقة بايتياً لنسخة 014 المركّبة سابقًا.
- **مدقق دائم جديد لعقد الإرجاع:** يفحص 1120 نداءً بلا أي خطأ، ويرفض نسخة Run 2 الحقيقية عند `Set Displayed Line:66` بالضبط. تواقيع الدوال الأصلية مأخوذة من جداول الانعكاس في الملف التنفيذي، وثبت أن K2_SetTimer يخزّن بنية بسيطة.
- **الاختبارات:** إعادة تشغيل المؤقت 500/500 مطابقة إطارًا بإطار، والتدقيق المستقل 16/16.
- **الحزمة:** حزمة التجهيز `builds/rtl_poc/r8b_runtime_staging_019/Dispatch_AR_R8b_P.pak` ‏(`1058eac4…f988`) غير مركّبة، وإجراء Run 5 في `RUN5_READY.md`.
- **نتيجة Run 4 (ينقلها المشرف عن المشغّل):** الحروف العربية ظاهرة في القوائم والإعدادات والترجمات، لكن الظهور التدريجي في Proto يجري من اليسار إلى اليمين مع تداخل، لذلك رُفض Proto الأصلي.
- قائمة مشكلات الواجهة والترجمة: `reports/TRANSLATION_UI_BACKLOG_019.md`.
- القيم: `ARABIC_GLYPH_RENDERING_PROVEN=true`، `ARABIC_FONT_RUNTIME_PARTIAL=true`، `STOCK_PROTO_RTL_REJECTED=true`، `R8B_FIXED=true`، `IN_GAME_RTL_PROVEN=false`، `final=0`.
- التفاصيل: `reports/rtl_research/renderer_repair/R8B_REPAIR_019.md`، والتقرير: `lastnews/report_019.md`.


**الأحدث: الجولة 018 — 2026-10-25:** `FONT_INSTALLED_RUNTIME_PENDING`، وRun 4 جاهز للمشغّل.

- بُني `builds/rtl_poc/font_runtime_018/Dispatch_AR_Fonts_P.pak` مرتين بايتياً بالتطابق: `b8b22bcb0d6f4fd31963a2743c12c822273cc54cc983947e7a0997bda07db19f`، 62,412 بايت.
- محتواه 3 uasset + 3 uexp فقط للمركّبات Montserrat/Orbitron/Rajdhani في المسارات الأصلية؛ الملفات الستة المستخرجة متطابقة مع نموذج 017. المدقق على النموذج والمستخرج: `FONT_FIX_017_STATIC_PASS`، صفر أخطاء و5/5 حالات سلبية.
- رُكبت حزمة Fonts وحدها بعد إغلاق Steam والتحقق من بصمات EXE وpakchunk0 وTexts. نُسخت Config وSaveGames احتياطياً مع تحقق SHA256 إلى `backups/runtime_run4_018_20261025_083606_164/`؛ الحفظ والإعدادات والملفات الأصلية بلا تغيير.
- الحالة عند التسليم: Texts + Fonts + `-culture=ar`، R8b وLocmeta غائبان، اللعبة لم تُشغّل. إثبات ظهور الحروف واختبار الإنجليزية ينتظران المشغّل؛ `ARABIC_GLYPH_RENDERING_PROVEN=false`، `R8B_FIXED=false`، `IN_GAME_RTL_PROVEN=false`، `final=0`.
- الإجراء والأدلة وإيصال التركيب: `builds/rtl_poc/font_runtime_018/RUN4_READY.md` و`install_receipt.json` و`PRE_RUN4_HASHES.json`. آخر تقرير تجهيز وتركيب محفوظ في `lastnews/report_018.md`؛ نتائج العربية والإنجليزية معلّقة، ويُحدّث التقرير بعد نتيجة المشغّل.

**الجولة 017 — 2026-10-25:** مشكلتان منفصلتان.

**أ. انهيار R8b:** `R8B_FRAME_LAYOUT=EXACT_MISMATCH_FOUND`.
- التعليمة 66 في `Set Displayed Line` تستدعي `Build Arabic Timing` كجملة مستقلة خارج أي `Let`.
- هذه الدالة تُرجع FString عبر `CPF_ReturnParm`، فينسخ الآلة الافتراضية النص المبني في مخزن مؤقت غير مهيّأ على المكدس.
- في التفريغ يحوي هذا المخزن مؤشرًا إلى `ARText`، فكُتب النص (144 بايت) فوق إطار الدالة حتى `FFrame.Code` (= Rax).
- الإصلاح الأصغر: حذف قيمة الإرجاع من `Build Arabic Timing` (`ArabicReveal.cs:60`)، أو تغليف الاستدعاء في `Let` (`ArabicReveal.cs:140`). لم يُعَد البناء.

**ب. اختفاء الحروف العربية:** `ARABIC_FONT_ROUTE=IDENTIFIED`.
- الخطوط المركّبة Montserrat/Rajdhani/Orbitron بلا نطاق عربي، واحتياطيّها NotoSansCJK بلا حروف عربية.
- لا يوجد احتياط مترجم ولا LastResort في هذا الإصدار، لذلك تُسقَط الحروف العربية وتظهر علامات الترقيم وحدها.
- النموذج المنفصل `builds/rtl_poc/font_fix_017/` يضيف نطاقًا عربيًا واحدًا يشير إلى ملف Naskh الذي تشحنه اللعبة. نتيجته `FONT_FIX_017_STATIC_PASS`، وهو غير مركّب.

القيم الحالية: `R8B_RUNTIME_FAULT_CONFIRMED=true`، `ARABIC_CULTURE_PROVEN=true`، `ARABIC_LOCRES_PROVEN=true`، `ARABIC_GLYPH_RENDERING_PROVEN=false`، `IN_GAME_RTL_PROVEN=false`، `final=0`.
التقرير: `lastnews/report_017.md`.

**الجولة 011 — 2026-10-25:** `R8B_WBP_STAGE2_REVEAL_PARTIAL`.
تولّدت دوال التقدّم والإنهاء مرة واحدة والتخطي والتنظيف وإعادة الاستخدام ومزامنة الحجم والحدود والالتفاف.
نجحت 19 حالة في نموذج التعليمات المولّدة و6 حالات سلبية، مع صفر أخطاء بنية وحتمية وإعادة حفظ متطابقة. الفحص الشامل STATIC_PASS 27/27.
الأصل `builds/rtl_poc/reveal_control_011/` منفصل وغير قابل للتركيب. ملفات المرحلتين السابقتين الـ79 محفوظة.
العائق الأصغر: تحديد محرّك تجميع زمن Proto أثناء الإيقاف عند+0x86c وربط مصدر زمن مكافئ؛ لا يوجد نداء محرك مربوط.
اختبار الزمن المحقون لا يثبت التكافؤ داخل اللعبة. التفاصيل: `WBP_REVEAL_RESULT_011.md` و`SCHEDULER_TIMING_011.md`.
لم تُشغّل اللعبة أو Steam ولم تُركّب حزمة؛ `tested_in_game=0` و`final=0`.

**الجولة 010 السابقة — 2026-10-25:** نجحت تهيئة المرحلة الثانية خارج اللعبة، `R8B_WBP_STAGE2_PASS` ضمن نطاق التهيئة فقط.
أُضيف فرع اللغة `ar/ar-` بعد معالجة الألفاظ، والتقطيع الكامل والوسوم واختيار النمط وتهيئة العتبة والنص مرة واحدة لكل طبقة.
تغيّرت دالتا العرض والإيقاف عمدًا؛ الدوال الأخرى الـ19 وملفات المرحلة الأولى الـ62 لم تتغير. صفر تغييرات غير متوقعة.
نجحت 96 مقارنة مع مرجع التقطيع، و39 حالة للعتبة، والحالات السلبية الست، وحتمية الملفات وإعادة الحفظ.
مؤقت الكشف وArabic Step/Finish لم يُولّدا بعد؛ الأصل المنفصل `builds/rtl_poc/stage2/` غير قابل للتركيب وغير مختبر داخل اللعبة.
التفاصيل في `WBP_STAGE2_RESULT.md` وتقرير المشرف `lastnews/report_010.md`؛ تبقى `tested_in_game=0` و`final=0`.

**الأحدث: الجولة 009 — 2026-10-25:** `R8B_WBP_STAGE1_PASS` للتحقق خارج اللعبة فقط.
تولّدت أربع جداول عربية (38 صفًا لكل جدول، 28/36) ونسخة واجهة منفصلة تضم سبعة عناصر عربية وسبع فتحات ربط، كلها مخفية افتراضيًا.
الفاحص: صفر أخطاء، صفر تغييرات أصلية غير متوقعة؛ 34/37 كائنًا أصليًا متطابقة بايتًا ببايت، وتعليمات الدوال الأصلية الـ21 محفوظة مع بصماتها.
التوليد مرتين وإعادة الحفظ متطابقة، واكتُشفت الحالات السلبية العشر. الفحص العام `STATIC_PASS` ‏25/25.
الأصول في `builds/rtl_poc/stage1/` موسومة NOT_INSTALLABLE/NOT_RUNTIME_TESTED. لا تعديل Kismet في هذه الجولة.
التالي: مولّد وفاحص Kismet للمرحلة الثانية وفق `reports/rtl_research/renderer_repair/WBP_STAGE2_BYTECODE_MAP.md`.
ربط المتغيرات وقت التشغيل، الحدود على 4.27، المؤقت/الإنهاء والتجميع داخل اللعبة غير مثبتة؛ تبقى `tested_in_game=0` و`final=0`.
الدليل: `WBP_STAGE1_RESULT.md` و`stage1_verification.json`؛ تقرير المشرف `lastnews/report_009.md`.

تاريخ التقرير: 2026-10-24، Asia/Riyadh.

**حالة الجولة 008 (الأحدث):** القرار `EDITOR_RENDERER_ROUTE_NEEDS_REVISION`.
- **المراجعة R8:** حُدّد التعديل R8 ونُفّذ في المحاكاة ونجح على UE 5.8.4 فقط. يحلّ R8 محلّ هدف العرض (RT) في الجولة 007: العتبة الآن لكل كتلة في لون صبغة Border مستقل.
- **السبب:** مجمع الكتل في `WBP_SubtitlesWidget` غير محدود، وقد تظهر عدة كتل معًا. كما أن صفوف DataTable ترتبط بخامة ثابتة.
- **أدلة جديدة من ملفات اللعبة نفسها:** خامة الترجمة المشحونة `M_SubtitlePrinting` تستقبل لون الرأس. شيفرة الـVS تفك sRGB بدقة. الـPS يقسم اللون على VertexColor، ثم يضرب Slate الناتج فيه. لذلك صنّفت G1 وG2 وG3 لـ4.27 `HIGH_CONFIDENCE`.
- **المحاكاة الرقمية:** 256/256 بثوابت الـVS المشحونة.
- **التقطيع:** 7,488 ترجمة، وأقصى عدد وحدات 69.
- **المتغيّر R8b:** يعيد استخدام خامة اللعبة نفسها بلا أي شيدر جديد، وحده 37 وحدة. يتأثر به 20 سطرًا فقط. هو المسار الوحيد الذي يمكن إنتاج كل أصوله دون محرر 4.27.
- **ما بقي:** توليد تعديل `WBP_SubtitleBlock` (`POSSIBLE_BUT_UNPROVEN`) وكل التحقق داخل اللعبة.
- **التفاصيل:** `reports/rtl_research/renderer_repair/COMPATIBILITY_AUDIT_008.md`.

لم تُشغّل اللعبة ولا Steam ولم تُركّب أي حزمة. `tested_in_game=0`، `final=0`. التقرير: `lastnews/report_008.md`.

**حالة الجولة 007 (السابقة):** طُلب محرر UE4.27، لكن التثبيت عبر Epic Launcher أنتج **UE 5.8.4** في `D:/EPIC/UE_5.8`، واختار المستخدم إجراء الاختبار عليه هذه الجولة. لذلك `UE427_EDITOR_READY=false` وتصنيف 4.27 هو `STOCK_RENDERER_GATE_TEST_BLOCKED`: G1/G2/G3 ما زالت `NOT_PROVEN` وG4/G5 `NOT_RUN` على 4.27.

على 5.8.4 فقط (غير معتمد لـ4.27) نجحت البوابات الخمس في مشروع معزول `tools/ue427_stock_reveal_test`:
- G1: لون الـrun يصل إلى خامة الخط كـVertexColor، والقناع مطابق.
- G2: ترميز بايت sRGB بلا فقد، وسعة 255 وحدة مقابل حاجة 69.
- G3: 12/12 سطرًا للواجهة وللظل داخل RetainerBox، بلا أي SetText بعد التهيئة، وبلا اختلاف بين الواجهة والظل.
- G4: الطبخ ناجح.
- G5: إعادة الاستخدام بلا بقايا.

اكتشافات تغيّر التصميم: Slate يضرب ناتج الخامة في لون الرأس فيجب القسمة عليه، وRetainerBox يحتاج RequestRender مع كل تحديث للعتبة ومرة بعد SetText، وأي تلوين RGB لعنصر أب يُفسد الفهرس. الأدلة في `reports/rtl_research/renderer_repair/ue427_gate_test/`.

لم تُشغّل اللعبة ولا Steam، ولم تُركّب أي حزمة. `tested_in_game=0`، `final=0`. التقرير: `lastnews/report_007.md`.

**حالة الجولة 006 (الأحدث، تُلغي الأرقام الأقدم أدناه):** `STATIC_PROJECT_COMPLETION_SWEEP_PARTIAL`. الترجمة 12,973 مدخلًا (12,487 تغيّر إلى العربية و486 قيمة تقنية باقية). نطاق المحرك صار 464 مفتاحًا بعد إضافة 4 مفاتيح مؤكدة التشغيل. المراجعة: حكم مراجعة على كل المدخلات الـ12,973، منها `reviewed=12955` (12,493 سليم و462 مصحح) و18 تحتاج سياقًا داخل اللعبة. المراجعة أجراها نموذج ذكاء اصطناعي تحليليًا، دون سياق داخل اللعبة ودون مراجع بشري ناطق بالعربية. سُجّل 534 تصحيحًا في `translation/review/changes.json`، أغلبها تطابق الجنس مع المتحدث والمخاطَب، وتشكيل 138 لافتة حالة بالمبني للمجهول. صفر أخطاء تحقق، وصفر أشكال عرض أو محارف اتجاه، وصفر رموز ناقصة في سلسلة الخطوط. تقارير التغطية في `reports/coverage/`: المحرك، والنصوص المطبوخة، و995 خامة، و3,436 فيديو. الحزمة الجديدة حتمية البناء: ZIP `190497af…` وPAK `0fa5792a…`، بالوسوم STATIC / EXPERIMENTAL / NOT_INSTALL_TESTED / NO_RTL_FIX، وتدقيقها في `reports/build/PACKAGE_AUDIT.md`. ما زال الظهور من اليمين إلى اليسار غير محلول، والحزمة لم تُركّب، واللعبة وSteam لم يُشغّلا، و`tested_in_game=0` و`final=0`. التقرير: `lastnews/report_006.md`، والمصفوفة: `reports/PROJECT_COMPLETION_MATRIX.md`.

**حالة الجولة 005:** `UE427_EDITOR_NOT_FOUND` → `STOCK_RENDERER_GATE_TEST_BLOCKED`، والسبب `GATE_TEST_BLOCKED_NO_UE427_EDITOR`. لم يُعثر على محرر UE4.27 في السجلات وتسجيلات Epic والمسارات المعروفة/المخصصة المفحوصة. لم يُنزّل أو يُثبّت شيء. G1/G2/G3 جميعها `NOT_PROVEN`؛ لم يُنشأ مشروع اختبار أو لقطات/فروق بكسل. استنتاجات الجولة 004 باقية كما هي على مستوى التصميم، بلا إعادة تحليل. `GAME_NOT_RUN`، `STEAM_NOT_RUN`، `PACKAGE_NOT_INSTALLED`، `tested_in_game=0`، `final=0`. تقرير الجولة في `C:\Users\USER\OneDrive\Desktop\lastnews\report_005.md`.

**آخر نتيجة — الجولة 004:** `STOCK_ENGINE_REPAIR_ROUTE_IDENTIFIED` على مستوى التصميم فقط، غير مثبت. لا يوجد مسار لتحميل وحدة native جديدة في هذا الإصدار (`NATIVE_MODULE_LOADING_NOT_FOUND`)، لذا سُحب اقتراح الـ widget الأصلي من الجولة 003. المسار المقترح يستخدم فئات المحرك الموجودة أصلًا: URichTextBlock مع خامة كشف تقرأ عتبة من render target. التفاصيل في قسم Round 004 أدناه.

**نتيجة الجولة 003:** `RENDERER_REPAIR_PROTOTYPE_BUILT` لنموذج مستقل فقط، لا كود Unreal مركب. يثبت ثبات المواضع والكشف الآمن في النموذج. المسار الأصلي وحزم اللعبة لم تتغير؛ الربط الأصلي وعزل العربية ما زالا غير مثبتين. التفاصيل والحدود في قسم Round 003 أدناه.

**تحديث الجولة 002:** `PAINT_MODEL_LOGICAL_PEN` و`ZERO_INTERVAL_BATCHES_CHARACTERS` مثبتان من مسارات الملف التنفيذي الحالي. القرار `WORD_REVEAL_REJECTED` لحل التوقيت وحده، ويتجاوز قرار `WORD_REVEAL_BLOCKED` السابق: تجميع الأحرف لا يصلح مواضع رسمها. غياب المصدر لم يمنع هذين التصنيفين. الأدلة: `reports/rtl_research/proto_binary/`.

الجولة 002 تحليل ثابت فقط، بلا إصلاح مدمج أو تشغيل أو تركيب. عزل العربية `ARABIC_ISOLATION_NOT_PROVEN`، و`tested_in_game=0` و`final=0`. فحص SHA256 جديد لجميع ملفات اللعبة الـ97 مطابق للأساس، بلا إضافات أو ملفات مفقودة. التفاصيل السابقة أدناه تسجل حالة الجولات السابقة، وتُقرأ في ضوء هذا التحديث.

**اكتمل إعداد حزمة نصوص تجريبية لـ12,969 مدخلًا:** 12,483 مدخلًا تغيّر إلى العربية، و486 قيمة تقنية/اسم مفتاح/علامة بقيت كما ينبغي. فحوص البنية: صفر أخطاء وصفر تحذيرات.

**التعريب الكامل غير منجز بعد:** الظهور العربي التدريجي داخل ProtoAnimatedText ما زال غير محلول داخل اللعبة. حُددت نقطة التحكم، وبُني لها نموذج مرجعي مستقل مختبر، لكنه ليس كود لعبة. لم تُركب الحزمة، ولم تُشغل اللعبة. لا يوجد نجاح بصري أو اعتماد FINAL.

## Completed

- تحديد مسار اللعبة وإصدارها ومحرك UE4.27 ونظام الحزم والنصوص والخطوط والواجهة والصوت.
- قراءة فهارس 20 حزمة مشفرة والتحقق من SHA1 لكل فهرس؛ جرد 62,861 مدخلًا.
- استخراج 607 ملفات مرجعية مع بصمات SHA256، وبقاؤها جميعًا بلا تغيير.
- ترجمة جميع جداول المشروع المختارة والحلقات 1–8، ورسائل إضافات الاتصال، ومجموعة 460 مفتاح نظام/تحكم محددة من المحرك.
- الاحتفاظ بالإنجليزية والمفاتيح والسياق والمتحدث المتاح، والمسرد ودليل الأسلوب.
- توحيد 61 صفًا للأسماء بعد الدمج، وإعادة المرجع المحدد لخطة 401(k) بعد فحص المحتوى.
- إنشاء أدوات الاستخراج والتحقق والبناء والتركيب والإزالة الآمنة الاختيارية، والتقارير.
- بناء PAK إضافي للغة ar فقط والتحقق من سلامة ZIP والمثبّت المستقل على ملفات وهمية.
- **(جديد)** تحديد نقطة التحكم في الكشف المشترك: رسم run الخاص بـ ProtoRichTextCharColorDecorator في الكود الأصلي (native). الأدلة والمسارات المرفوضة في docs/RTL_IMPLEMENTATION.md.
- **(جديد)** نموذج مرجعي مستقل `tools/rtl_reveal/` يعمل بـ HarfBuzz وUBA كامل. يبني التخطيط النهائي مرة واحدة: تشكيل، BiDi، التفاف عند 1050، ومحاذاة يمنى. بعدها يكشف وحدات تجمع grapheme clusters مع shaping clusters، في الترتيب المنطقي وبتوقيت Proto الأصلي. يُعيد None لغير العربية.

- **(جديد، جولة word-reveal)** النتيجة: `WORD_REVEAL_BLOCKED`. حقول توقيت Proto مثبتة من DataTable الفعلي. بُنيت نسخة POC منفصلة غير مركبة لـ `DT_SubtitlesProtoRichText[_Large]`، وفيها letter=0 وanim=0 وadvanced=true وspace=0.16. round-trip نظيف: 56+28 فرقًا مقصودًا فقط وصفر فروق غير مقصودة. نموذج التوقيت آمن على shaping clusters في 42/42 نصًا. لكن نموذج الرسم المنشور يفشل BiDi في 42/42 نصًا، وسلوك 1.02 الفعلي غير مثبت، وعزل العربية `NOT_PROVEN`. التفاصيل في docs/RTL_IMPLEMENTATION.md.

## Current work / unresolved work

الخوارزمية المطلوبة محددة ومختبرة خارج اللعبة. التطبيق داخل اللعبة يتطلب تعديل رسم run في الإضافة بحيث:
1. يرسم كل glyph في موضعه من التسلسل المشكَّل بالترتيب البصري.
2. يأخذ alpha آخر وحدة UTF-16 في وحدة الكشف الخاصة به.

يبقى العداد الأصلي والأحداث والتوقيت وBlueprint والإنجليزية بلا تغيير.

## Blocker

1. إصلاح الرسم غير مدمج بعد. مصدر ProtoAnimatedText 1.02 غير موجود، لكنه لم يعد شرطًا لتصنيف السلوك الذي أُنجز من الملف التنفيذي. الحاجة الفعلية إليه للتعديل/الدمج لم تُحسم.
2. مسار تحميل كود مثبت التوافق مع Dispatch-Win64-Shipping.exe. البناء monolithic، ولا يوجد DLL للإضافة ولا PDB، ولا UE4SS أو proxy DLL مثبت.
3. اختبار تشغيل فعلي، وهو ممنوع حاليًا.

## Discovered issues

- الوثائق الرسمية للإضافة تذكر عدم دعم العربية في الطباعة حرفًا حرفًا. تعديل المحاذاة وحده لا يحل ذلك.
- الدرس المنشور لمؤلف الإضافة يقسم السطر المشكَّل إلى شرائح بحجم وحدة UTF-16، ويحرك القلم من اليسار إلى اليمين بالترتيب المنطقي. هذا يفسر انعكاس ترتيب العربية مع بقاء أشكال الربط، ويفسر غياب glyph مستقل للألف في لام ألف. النموذج يؤكد هذا السلوك: الإنجليزية تطابق، والعربية تنعكس. الكود الفعلي للإصدار 1.02 لم يُرَ.
- قص مستطيل واحد من اليمين لا يكفي مع النصوص المختلطة، مثل `250 XP`. هذا مثبت في الاختبار.
- تجربة Blueprint المعزولة مستبعدة من التوزيع لأنها تغيّر الإنجليزية ولا تصلح الظهور التدريجي، ولا يعمل جعل Blueprint محليًا بمجرد نسخه إلى L10N/ar.
- تفعيل الثقافة ar داخل اللعبة وقائمة اختيار اللغة غير متحققين.
- هناك 19,822 مدخلًا خارج مجموعة المحرك المختارة، و30 مفتاحًا في manifest دون English locres، ونصوص صور/فيديو/نصوص صلبة لا يجوز ادعاء اكتمالها.
- الترجمة مؤلفة وليست مراجعة مشهدية كاملة؛ reviewed/tested/final=0.

## Modified files

الكتابة داخل Dispatch_AR فقط. هذه الجلسة: `tools/rtl_reveal/reveal.py` و`tools/rtl_reveal/test_reveal.py` و`reports/rtl_research/reveal_model/` (جديدة)، و`docs/RTL_IMPLEMENTATION.md` و`docs/KNOWN_ISSUES.md` و`docs/TESTING.md` و`reports/FINAL_VERIFICATION.json` (حقلان جديدان) وهذا الملف. **صفر تعديلات على ملفات تثبيت اللعبة، ولا تركيب فعلي للحزمة، ولا تغيير في PAK أو ZIP أو الترجمة.**

## Tests performed

- 97 ملفًا أصليًا موجودة كما في الأساس، دون ملفات مضافة أو ناقصة (مقارنة قائمة الملفات؛ لم يُعَد حساب البصمات الكبيرة في هذه الجلسة).
- 607 مراجع مستخرجة مطابقة لبصماتها الأصلية.
- 14 موردًا مترجمًا؛ فك/تركيب locres مع حفظ المفاتيح وبصمات المصدر، وتجميع قابل للإعادة.
- كل 12,969 سجل يحتفظ بالإنجليزية الأصلية؛ الوسوم والمتغيرات والفواصل وCR/LF/tab/backslash والترميز سليمة.
- 3 حزم بيانات PoC، وتحقق تطابق البايتات بعد قراءة الحزمة، وتطابق مخرجي PAK متتاليين.
- فحص ZIP وتشغيل اختبار المثبّت على ملفات وهمية من النسخة المحمولة؛ بلا تشغيل لعبة.
- 105 ملفات خطوط: cmap/OpenType/metrics فقط؛ ليست نتيجة اختبار بصري.
- **(جديد)** `tools/rtl_reveal/test_reveal.py`: PASS. يشمل 9 حالات × غلافين × وضعين، وفحوصًا موجهة، وضابطين سلبيين. أُدخلت 5 أعطال متعمدة وفشل الاختبار عند كل منها.
- **(جديد)** فحص عدم وجود مفتاح AES، خامًا أو hex، في builds/reports/docs/translation/tests/tools/rtl_reveal: لا نتائج.

## Failed tests / unresolved acceptance

لا توجد أخطاء بنيوية حالية. الاختبارات البصرية والحركية داخل اللعبة **NOT_RUN**، والظهور العربي التدريجي داخل اللعبة **UNRESOLVED**. نجاح النموذج المرجعي لا يُعد PASS للعبة.

## Outputs

- builds/Dispatch_AR_Texts_EXPERIMENTAL.zip (SHA256 `bcbcc5a1a47dd1b6f9be51209779d98bc92afb1c0296c17c26d767c81d1e9aea`)
- builds/arabic_texts_experimental/Dispatch_AR_Texts_P.pak (SHA256 `3155fa9e4060f9c26b84cdc90cb9c18a49f48d00bf9626a50fad5a5207c585b4`)
- translation/MASTER_TRANSLATION.md، translation/progress.json
- reports/FINAL_VERIFICATION.json
- tools/rtl_reveal/، reports/rtl_research/reveal_model/ (إطارات SYNTHETIC وليست صور لعبة)

## Next step

مراجعة مستقلة لحزمة `reports/rtl_research/proto_binary/` ونتيجة رفض حل التوقيت وحده. حُددت بالفعل vtable الـ run ودالة الرسم؛ لا يُعاد التحقيق من الصفر. يحدد المشرف بعدها مسار إصلاح الرسم المشروط بالعربية واحتياج الدمج. المصدر المرخص خيار مفيد للتعديل، وليس شرطًا للتصنيف المنجز. لا تشغيل أو تركيب أو DLL أو hook في الجولة الحالية.

## Round 002 outputs

- `tools/proto_binary_analysis/evidence.py`: أداة جديدة تقرأ EXE فقط؛ تتحقق من 8 حقول و8 روابط مؤشرات و21 نطاق دالة و13 تعليمة حاسمة. الأدوات الثلاث السابقة لم تتغير.
- `reports/rtl_research/proto_binary/`: النتائج، سلسلة تسجيل المزيّن، الإزاحات، xrefs، مقاطع التفكيك المحدودة، وفحص السلامة لكل ملفات اللعبة الأصلية.
- تحديث وثائق RTL/المشكلات/الاختبار؛ نسخها السابقة في `backups/session_002_docs/`.
- تقرير المشرف: `C:\Users\USER\OneDrive\Desktop\lastnews\report_002.md`.
- لا تغييرات على الترجمة أو PAK/ZIP أو تجارب DataTable السابقة. لا نجاح بصري مزعوم.

## Round 003 — detached renderer repair prototype

Result: `RENDERER_REPAIR_PROTOTYPE_BUILT` (Python/SVG/PNG, not an Unreal module). Architecture: an Arabic-only UWidget wrapping custom Slate with retained final text layout and one shared foreground/shadow reveal mask. English remains on the existing Proto path by design; native registration/loading and Blueprint routing have not been implemented.

The two existing WBP exports contain no ready culture branch, WidgetSwitcher or spare ordinary text widget; the two text properties are typed as ProtoRichTextBlock. Classification: `ARABIC_BRANCH_REQUIRES_NATIVE_INTEGRATION`, with Blueprint code changes also required for the new-widget route. `ARABIC_ISOLATION_NOT_PROVEN` remains unchanged.

The new harness reuses the same 14 corpus texts and 3 wrappers, without rebuilding or tuning the old timing POC. 42 placement cases, 84 cluster/word plans and 2,908 reveal frames pass: zero cluster splits, geometry/wrap drift or shadow-mask drift; correct model placement passes 42/42 and the logical-pen abstraction fails 42/42. Ten generated JSON/SVG/PNG artifacts are byte-identical across repeated builds. No shaping occurs during reveal.

Limits: existing simplified wrapping/fallback, fixed-size style metrics, unverified native donthide/timing adapter, font material/atlas/RetainerBox bridge and new-class deployment. UE4.27 headers/UBT were not discovered in checked registered/known roots. No native UE build occurred. No Proto source requirement is asserted for the independent design.

Details: `reports/rtl_research/renderer_repair/ARCHITECTURE.md`, `integration_points.json`, `SOURCES.md`, `prototype/validation.json`, and `verification.json`. Commands:

```powershell
python -X utf8 tools/rtl_renderer_prototype/inspect_assets.py
python -X utf8 tools/rtl_renderer_prototype/build.py
```

The round does not access original game files; round 002's 97-file integrity verification is reused without recomputation. No Blueprint, game files, distributions or translation data changed. `GAME_NOT_RUN`, `STEAM_NOT_RUN`, `PACKAGE_NOT_INSTALLED`, `IN_GAME_RTL_NOT_PROVEN`, `tested_in_game=0`, `final=0`.

## Round 004 — architecture gate review (Opus 5.5)

Result: `STOCK_ENGINE_REPAIR_ROUTE_IDENTIFIED` at design level only, NOT proven. Classifications: STOCK_RENDERER_ROUTE=NOT_PROVEN; BLUEPRINT_ARABIC_BRANCH=REQUIRES_UNSUPPORTED_EDIT (current UAssetAPI tooling); EXISTING_NATIVE_CLASS_ROUTE=REJECTED; NATIVE_MODULE_LOADING=NOT_FOUND; CUSTOM_NATIVE_RENDERER=BLOCKED_BY_DELIVERY.

The round-003 native widget is withdrawn as the recommendation. The shipping EXE is monolithic: FStaticallyLinkedModuleRegistrant RTTI, 0 engine C++ exports, no module DLLs or `.modules` manifests, no script runtime. Plugin discovery (Mods/, AdditionalPluginDirectories) carries content only. A new UClass cannot be loaded without EXE change, proxy DLL, UE4SS or injection.

Replacement design: stock URichTextBlock final Slate layout, one rich run per whitespace word unit, unit index encoded in each style row's colour, a new UI font material that shows a glyph only when its unit index <= a threshold read from a cooked render target, and the threshold written per step with stock ClearRenderTarget2D. Text is set once per line; steps never relayout. All native pieces are present by reflected name (`exe_names.json`). ProtoRichTextBlock is a URichTextBlock subclass (asset evidence). Gates G1–G5 (font-material vertex colour/coverage, quantization, RT update under RetainerBox, shader delivery, pooling/tint) are untested and need a UE4.27 editor.

Detached run-boundary test: cuts at whitespace give identical geometry 40/40 (with and without HarfBuzz context). Cuts at punctuation drift 10/20 (Latin kerning loss, script change in punctuation-only runs). The negative mid-word control is detected. Dynamic markup (per-step SetText) is REJECTED_AS_PRIMARY.

Details: `reports/rtl_research/renderer_repair/ARCHITECTURE_REVIEW_004.md`, `run_boundary.json`, `exe_names.json`. No game run, install, cook or Blueprint edit. `GAME_NOT_RUN`, `STEAM_NOT_RUN`, `PACKAGE_NOT_INSTALLED`, `IN_GAME_RTL_NOT_PROVEN`, `tested_in_game=0`, `final=0`.
