# DISPATCH — Full Arabic Localization Project

أنت المسؤول التقني الكامل عن مشروع تعريب لعبة **Dispatch** إلى اللغة العربية.

هدف المشروع ليس مجرد ترجمة النصوص، بل إنتاج تعريب عربي احترافي كامل يدعم:

- جميع الحوارات.
- القوائم.
- الخيارات.
- الترجمات أثناء المشاهد.
- النصوص التفاعلية.
- الإشعارات.
- أسماء المهام.
- الشروحات.
- Tutorials.
- UI.
- النصوص التي تظهر تدريجيًا.
- Arabic RTL.
- Arabic shaping.
- Fonts.
- Line wrapping.
- Text alignment.
- Typewriter / progressive text animation.

يجب أولًا تحليل اللعبة بالكامل وتحديد محرك اللعبة ونظام النصوص قبل تعديل أي شيء.

---

# 1. Project Safety

🟥 ممنوع تعديل ملفات اللعبة الأصلية مباشرة بدون Backup أو طريقة Restore واضحة.

أنشئ Workspace مستقل مثل:

```text
Dispatch_AR/
├── docs/
├── extracted/
├── translation/
├── fonts/
├── tools/
├── scripts/
├── patches/
├── tests/
├── builds/
├── backups/
└── reports/
```

احتفظ دائمًا بنسخة من الملفات الأصلية التي يتم التعامل معها.

لا تعمل تغييرات عشوائية داخل ملفات اللعبة.

كل تغيير يجب أن يكون:

```text
identified
documented
tested
reversible
```

---

# 2. Initial Investigation

في البداية لا تبدأ بالترجمة.

افحص اللعبة بالكامل وحدد:

```text
Game Engine
Game Version
Text System
Localization System
Subtitle System
UI Framework
Font System
Text Rendering System
Text Animation System
Asset Packaging
Compression
Encryption
```

ابحث خصوصًا عن:

```text
Unity
Unreal Engine
Ink
Yarn Spinner
FMOD
Wwise
TextMeshPro
UGUI
Slate
UMG
Localization Tables
JSON
CSV
XML
YAML
SQLite
Binary localization files
Custom dialogue formats
```

أنشئ تقرير:

```text
docs/TECHNICAL_ANALYSIS.md
```

يحتوي على جميع الاكتشافات.

---

# 3. Find ALL Game Text

ابحث عن جميع مصادر النصوص داخل اللعبة.

لا تفترض أن ملفًا واحدًا يحتوي كل شيء.

صنف النصوص:

```text
Dialogue
Subtitles
Choices
UI
Menus
Settings
Tutorials
Notifications
Objectives
Character Names
Locations
Items
Descriptions
Achievements
Credits
System Messages
Phone / Computer UI
Interactive Text
Cinematic Text
```

أنشئ Inventory كامل:

```text
docs/TEXT_INVENTORY.md
```

ويجب أن يحتوي على:

```text
source file
format
number of strings
category
encoding
can be safely modified?
requires repacking?
RTL status
```

---

# 4. Translation Master File

أنشئ ملف ترجمة مرجعي كامل.

مثال:

```text
translation/MASTER_TRANSLATION.md
```

كل سطر يجب أن يحتوي النص العربي أولًا ثم النص الإنجليزي الأصلي تحته.

مثال:

```text
[ID: DIALOGUE_001245]

AR:
لا أعرف ماذا تريد مني.

EN:
I don't know what you want from me.
```

لا تحذف النص الإنجليزي أبدًا من ملف المرجع.

يكون لدينا دائمًا:

```text
Arabic
English Original
String ID
Source File
Context
Speaker
Status
Notes
```

مثال:

```text
ID: DLG_004821
Speaker: Robert
Context: Police station conversation
Status: translated

AR:
ماذا حدث هنا؟

EN:
What happened here?
```

---

# 5. Arabic Translation Rules

الترجمة يجب أن تكون عربية طبيعية وليست ترجمة حرفية.

حافظ على:

```text
Character personality
Humor
Sarcasm
Emotion
Context
Timing
Meaning
Choice consequences
```

لا تترجم أسماء الشخصيات عشوائيًا.

أنشئ:

```text
translation/GLOSSARY.md
```

للمصطلحات والأسماء المتكررة.

و:

```text
translation/STYLE_GUIDE.md
```

لتوحيد أسلوب التعريب.

---

# 6. CRITICAL — TRUE RTL SUPPORT

هذه أهم نقطة في المشروع.

العربية ليست مجرد:

```text
text-align: right
```

أريد دعمًا حقيقيًا لـ:

```text
Right-To-Left
Arabic shaping
BiDi
Correct punctuation
Numbers
English mixed with Arabic
Line wrapping
Text animation
```

🟥 ممنوع حل المشكلة عن طريق:

```text
Reverse(string)
```

أو قلب الأحرف يدويًا.

هذا يسبب مشاكل في:

```text
Arabic shaping
English
Numbers
Punctuation
Mixed text
Unicode
```

استخدم نظام Unicode / BiDi صحيح.

---

# 7. CRITICAL — Progressive Dialogue Must Start From RIGHT

اللعبة تحتوي على نصوص حوار تظهر تدريجيًا.

النظام الإنجليزي غالبًا يعمل هكذا:

```text
H
He
Hel
Hell
Hello
```

ويظهر النص بصريًا:

```text
LEFT → RIGHT
```

باللغة العربية لا أريد هذا السلوك.

أريد النص العربي يبدأ من **يمين مربع الحوار** ويتوسع باتجاه اليسار:

```text
RIGHT ← LEFT
```

مثال الجملة:

```text
مرحبًا بك في المنزل
```

أثناء ظهورها التدريجي، أول حرف/كلمة يجب أن تظهر عند الجهة اليمنى.

ثم يتقدم النص باتجاه اليسار.

Visual behavior:

```text
                         م
                        مر
                       مرح
                      مرحب
                     مرحبًا
```

وليس:

```text
م
مر
مرح
مرحب
مرحبًا
```

من الجهة اليسرى للعنصر.

---

# 8. RTL Typewriter / Reveal System

ابحث تحديدًا عن الكود المسؤول عن:

```text
Typewriter Effect
Text Reveal
Visible Characters
Max Visible Characters
Substring
Character Counter
Dialogue Animation
Subtitle Animation
Text Mesh
Letter Reveal
```

ثم عدله ليعرف اللغة الحالية.

Pseudo logic:

```text
if language == Arabic:
    enableRTL()
    alignment = Right
    revealDirection = RTL
else:
    useOriginalBehavior()
```

لكن لا تعتمد على قلب النص.

يجب أن يبقى النص في **logical Unicode order** الصحيح.

---

# 9. Arabic Grapheme Handling

🟥 لا تكشف النص العربي باستخدام byte-by-byte أو char-by-char بطريقة تكسر Unicode.

استخدم:

```text
Unicode Grapheme Clusters
```

لأن الحرف العربي قد يحتوي على:

```text
Base character
Diacritics
Combining marks
```

ويجب ألا تظهر الحركات منفصلة.

مثال:

```text
مُ
```

يجب التعامل معها كوحدة عرض واحدة قدر الإمكان.

---

# 10. Preferred Typewriter Strategy

أفضل طريقة إذا كان محرك النص يدعمها:

ضع الجملة كاملة داخل Text Renderer من البداية.

ثم استخدم خاصية مثل:

```text
maxVisibleCharacters
visibleGlyphCount
clip
mask
reveal progress
```

بدل إنشاء:

```text
Substring(0, count)
```

في كل Frame.

السبب:

عند إرسال جزء فقط من الكلمة العربية إلى الـ renderer قد تتغير أشكال الحروف أثناء ظهورها.

أريد تقليل هذه المشكلة.

---

# 11. Arabic Word Reveal Test

اختبر أكثر من Mode.

## Mode A

Character reveal:

```text
م
مر
مرح
مرحب
مرحبً
مرحبًا
```

## Mode B

Word reveal:

```text
مرحبًا

مرحبًا بك

مرحبًا بك في

مرحبًا بك في المنزل
```

إذا Character Reveal تسبب في:

```text
glyph reshaping
flickering
detached letters
layout jumping
```

استخدم **Word Reveal** للعربية إذا كان أفضل بصريًا.

---

# 12. Preserve Right Anchor

عنصر النص نفسه يجب أن يكون Anchored من اليمين.

مثل:

```text
Anchor: Right
Pivot: Right
Alignment: Right
Direction: RTL
```

بحيث زيادة طول النص لا تجعل بداية الكلام تتحرك من اليسار.

يجب أن تكون نقطة البداية ثابتة في الجهة اليمنى.

Concept:

```text
┌───────────────────────────────────────────┐
│                           مرحبًا بك        │
└───────────────────────────────────────────┘
                                            ↑
                                      Start Here
```

ثم:

```text
┌───────────────────────────────────────────┐
│                    مرحبًا بك في المنزل    │
└───────────────────────────────────────────┘
                                            ↑
                                  Same Right Anchor
```

---

# 13. Multi-Line RTL

اختبر الجمل الطويلة.

مثال:

```text
هذا نص عربي طويل لاختبار التفاف الأسطر
ومعرفة إذا كانت الجملة تبدأ من اليمين
بشكل صحيح.
```

كل سطر يجب أن يكون:

```text
Right aligned
RTL
Correctly wrapped
```

لا أريد:

```text
Line 1 = Right
Line 2 = Left
```

أو أن يتغير اتجاه الكلام بعد Line Break.

---

# 14. Arabic + English Mixed Text

اختبر:

```text
اضغط E للمتابعة
```

```text
افتح Dispatch Menu
```

```text
لديك 25 XP
```

```text
HP: 100
```

```text
RTX 4070
```

يجب ألا تصبح:

```text
E اضغط للمتابعة
```

بطريقة غير صحيحة.

طبق Unicode BiDi بشكل صحيح.

---

# 15. Punctuation Tests

اختبر:

```text
مرحبًا!
```

```text
ماذا؟
```

```text
هل أنت متأكد...؟
```

```text
(اختبار)
```

```text
[اختبار]
```

```text
"مرحبًا"
```

والرموز:

```text
:
;
-
—
…
%
+
/
\
```

وتأكد أن مواضعها صحيحة بصريًا.

---

# 16. Arabic Fonts

افحص الخطوط الأصلية.

تحقق من وجود Glyphs عربية:

```text
Arabic
Arabic Presentation Forms
Numbers
Punctuation
Latin
Symbols
```

إذا الخط الأساسي لا يدعم العربية، ابحث عن خط مناسب قانونيًا ومفتوح المصدر.

الأولوية لخطوط ذات مظهر مناسب للعبة.

يمكن دراسة:

```text
IBM Plex Sans Arabic
Noto Sans Arabic
Noto Kufi Arabic
Cairo
Tajawal
```

لكن لا تستبدل الخط مباشرة.

اختبر أي خط أولًا داخل اللعبة.

أنشئ:

```text
docs/FONT_ANALYSIS.md
```

---

# 17. Font Metrics

انتبه إلى:

```text
Ascender
Descender
Baseline
Font Size
Line Height
Kerning
Glyph spacing
Padding
Text clipping
```

الحروف مثل:

```text
ي
ج
ح
خ
م
ع
غ
```

يجب ألا يتم قصها.

---

# 18. UI RTL Strategy

ليس كل UI يحتاج Mirror كامل.

صنف العناصر إلى:

```text
Text-only RTL
Partial RTL
Full mirrored layout
Keep original layout
```

مثل القوائم قد تحتاج:

```text
Text Alignment = Right
Icons = Left of text
Navigation = unchanged
```

ولا تعكس:

```text
gameplay icons
controller buttons
maps
logos
art
```

إلا عند الحاجة.

---

# 19. Dialogue Choices

الاختيارات يجب أن تظهر مثل:

```text
                         نعم، سأذهب معك
                         لا، لن أفعل ذلك
                         أحتاج إلى التفكير
```

مع بقاء:

```text
Controller icons
Keyboard buttons
Selection indicator
```

في أماكن منطقية.

اختبر Hover و Selected و Disabled states.

---

# 20. Subtitle Timing

لا تغير:

```text
Dialogue timing
Voice timing
Cutscene timing
Subtitle duration
```

بسبب اختلاف طول العربية.

يجب أن يبقى الـ timing الأصلي إلا إذا ثبت أنه يحتاج تعديلًا.

---

# 21. Variables and Placeholders

🟥 لا تغير المتغيرات.

مثال:

```text
Hello {playerName}
```

يصبح:

```text
مرحبًا {playerName}
```

وليس:

```text
مرحبًا playerName
```

حافظ على:

```text
%s
%d
{0}
{1}
<color>
<size>
<br>
\n
\t
[VAR]
{{variable}}
```

وأي Tags خاصة بالمحرك.

---

# 22. Markup Validation

أنشئ Script يقوم بمقارنة Tags بين EN و AR.

مثال:

```text
EN:
Press <color=yellow>{KEY}</color> to continue.

AR:
اضغط <color=yellow>{KEY}</color> للمتابعة.
```

إذا Tag مفقود يجب أن يعتبر النص:

```text
INVALID
```

---

# 23. Automated Validation

أنشئ Scripts باللغة الإنجليزية.

مثال:

```text
scripts/validate_translation.py
scripts/check_placeholders.py
scripts/check_missing_strings.py
scripts/check_duplicates.py
scripts/check_rtl.py
scripts/check_encoding.py
```

يجب أن تكتشف:

```text
Missing Arabic
Missing English
Broken placeholders
Broken tags
Empty strings
Duplicate IDs
Encoding corruption
Arabic reversed manually
Untranslated strings
```

---

# 24. Translation Status

استخدم حالات واضحة:

```text
TODO
TRANSLATED
REVIEWED
TESTED
FINAL
```

أنشئ:

```text
translation/progress.json
```

ويحتوي مثلًا:

```json
{
  "total": 10000,
  "translated": 2500,
  "reviewed": 1800,
  "tested_in_game": 900
}
```

---

# 25. Screenshots and Visual Testing

أنشئ:

```text
tests/screenshots/
```

واختبر على الأقل:

```text
Short dialogue
Long dialogue
Two-line subtitle
Three-line subtitle
Dialogue choice
Settings menu
Notification
Tutorial
Character name
Arabic + English
Arabic + numbers
Arabic + punctuation
Arabic typewriter animation
```

---

# 26. RTL Test Sentences

استخدم هذه الجمل أثناء الاختبار:

```text
مرحبًا بك في عالم Dispatch.
```

```text
هل أنت متأكد من أنك تريد المتابعة؟
```

```text
اضغط E لفتح القائمة.
```

```text
حصلت على 1,250 XP.
```

```text
HP لديك الآن 75%.
```

```text
هذا اختبار طويل جدًا لمعرفة طريقة التفاف النص العربي داخل مربع الحوار والتأكد من أن جميع الأسطر تبدأ من الجهة اليمنى.
```

---

# 27. Typewriter RTL Acceptance Test

هذه نقطة نجاح أو فشل المشروع.

عندما يظهر:

```text
أنا لا أعرف ماذا حدث.
```

أريد أن تبدأ الرسوم المتحركة من أقصى اليمين.

ثم يمتد النص بصريًا نحو اليسار.

🟥 إذا بدأ أول حرف من اليسار ثم انتهى النص بمحاذاة يمين بعد اكتماله، فهذا **FAIL**.

🟥 إذا تم قلب الأحرف يدويًا، فهذا **FAIL**.

🟥 إذا أصبحت الحروف العربية منفصلة، فهذا **FAIL**.

🟥 إذا تغير ترتيب الأرقام والإنجليزية، فهذا **FAIL**.

🟩 النجاح يعني:

```text
Correct Arabic shaping
Correct BiDi
Right alignment
Right anchored layout
RTL progressive reveal
Correct punctuation
Correct mixed Arabic/English
Correct wrapping
```

---

# 28. Never Hardcode One Dialogue

لا تصلح Dialog واحد يدويًا.

ابحث عن System مشترك يمكنه دعم:

```text
ALL Arabic dialogues
ALL Arabic subtitles
ALL progressive text
```

الحل يجب أن يكون Systematic.

---

# 29. Arabic Detection

إذا كان نظام اللعبة لا يحتوي Localization State واضحًا، يمكن استخدام:

```text
CurrentLanguage
Locale
Language ID
```

وإذا لم يوجد إطلاقًا، يمكن كحل احتياطي اكتشاف Unicode Arabic ranges.

لكن الأفضل دائمًا:

```text
locale == ar
```

وليس فحص كل String باستمرار.

---

# 30. Do Not Break English

جميع تغييرات RTL يجب أن تعمل فقط للعربية.

يجب أن تبقى الإنجليزية:

```text
LEFT → RIGHT
```

بنفس شكل اللعبة الأصلي.

Architecture:

```text
English:
LTR
Left alignment
Original reveal

Arabic:
RTL
Right alignment
Arabic shaping
RTL reveal
```

---

# 31. Build Pipeline

أنشئ Build Pipeline واضح:

```text
Extract
↓
Translate
↓
Validate
↓
Compile
↓
Pack
↓
Install
↓
Test
```

ويفضل وجود:

```text
scripts/build.py
```

و:

```text
scripts/install.py
```

إذا كان ذلك ممكنًا تقنيًا.

---

# 32. Documentation

أنشئ:

```text
README.md
docs/
├── TECHNICAL_ANALYSIS.md
├── TEXT_INVENTORY.md
├── EXTRACTION.md
├── TRANSLATION_SYSTEM.md
├── RTL_IMPLEMENTATION.md
├── FONT_ANALYSIS.md
├── BUILD.md
├── INSTALL.md
├── TESTING.md
└── KNOWN_ISSUES.md
```

---

# 33. RTL_IMPLEMENTATION.md

اشرح بالتفصيل:

```text
Original LTR implementation
Arabic RTL implementation
Text rendering library
BiDi method
Arabic shaping method
Typewriter method
Anchor changes
Alignment changes
Line wrapping
Mixed text handling
Known limitations
```

---

# 34. Reports

بعد كل مرحلة حدث:

```text
reports/CURRENT_STATUS.md
```

يحتوي:

```text
Completed
Current work
Discovered issues
Modified files
Tests performed
Failed tests
Next step
```

---

# 35. Work Autonomously

لا تتوقف عند كل مشكلة صغيرة لتطلب مني ماذا تفعل.

قم بـ:

```text
Investigate
Reason
Test
Compare
Choose safest solution
Document
Continue
```

إذا وجدت عدة طرق، اختر الطريقة:

```text
least destructive
most maintainable
most reversible
best Arabic support
```

---

# 36. First Mission

ابدأ الآن فقط بالمرحلة التالية:

## PHASE 1 — Investigation

1. افحص مجلد Dispatch بالكامل.
2. حدد المحرك.
3. حدد ملفات النصوص.
4. حدد ملفات الخطوط.
5. حدد نظام الـ UI.
6. حدد نظام Dialog/Subtitles.
7. ابحث عن Progressive/Typewriter text logic.
8. حدد كيف يمكن تطبيق RTL.
9. لا تبدأ ترجمة آلاف الأسطر حتى ينجح Proof of Concept عربي.
10. أنشئ التقارير.

ثم نفذ:

## PHASE 2 — Arabic RTL Proof of Concept

اختبر جملة واحدة:

```text
مرحبًا بك في عالم Dispatch.
```

ويجب أن:

- تظهر العربية متصلة.
- تبدأ من اليمين.
- تمتد تدريجيًا إلى اليسار.
- تبقى نقطة اليمين ثابتة.
- تعمل علامات الترقيم.
- لا يتم قلب النص يدويًا.

بعد نجاح ذلك اختبر:

```text
اضغط E للمتابعة، لديك 250 XP.
```

ثم:

```text
هل أنت متأكد من أنك تريد الذهاب إلى Dispatch HQ؟
```

لا تبدأ Full Translation حتى تمر جميع اختبارات RTL.

بعد نجاح الـ Proof of Concept انتقل تلقائيًا إلى استخراج وترجمة اللعبة كاملة.
