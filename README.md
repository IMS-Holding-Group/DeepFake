# نظام كشف DeepFake

تطبيق ويب يقدّر احتمال أن تكون صورة أو فيديو مرفوعاً حقيقياً أو متلاعباً به. المسار الذي يخدم المتصفح هو الكشف والتحليل. لا يوجد في `app/api.py` ولا في `app/routes.py` مسار يصنّع وجهاً أو يبدّل وجهاً في وسائط.

## 1 ما هو المشروع

نظام محلي: المستخدم يرفع صورة أو فيديو، يحصل على رقم مهمة، ثم يقرأ درجة `real_score` و`fake_score` مع شروحات وملفات معاينة. التشغيل من `python run.py`. الواجهة العربية في `app/templates`.

README السابق يصف دقة عالية وشبكات EfficientNet جاهزة في المسار الرئيسي. الكود التشغيلي في `DeepFakeDetector` يبني `XceptionDetector()` بلا مسار أوزان مخصص، ويطبع عند البناء أنه يستخدم أوزان ImageNet فقط وأن طبقة التصنيف الإضافية لم تُدرَّب على بيانات تزوير ما لم يُمرَّر `weights_path`. EfficientNet وViT معرفان في `app/models/advanced_models.py` وغير مستدعين من `analyze_image`. دوال `train_xception` و`train_efficientnet` و`prepare_dataset` في ذلك الملف تحتوي `pass` وتعليقاً أن التنفيذ يوضع لاحقاً. لا تنزّل مجموعة بيانات ولا تدرّب.

## 2 لماذا وُجد

عرض تحليل محلي لوسائط مشبوهة دون إرسال الملف إلى خادم التحليل الأساسي. الخدمات الخارجية في `external_services.py` اختيارية وغير مربوطة بمسار الرفع الحالي.

الهدف الموثق سابقاً: واجهة عربية، درجة واقعية، وتقرير. التنفيذ الفعلي درجة بين حدين مع شروحات من عدة فحوص.

## 3 المستخدمون

زائر يفتح الموقع ويرفع ملفاً. لا جدول مستخدمين ولا تسجيل دخول في `routes.py` أو `api.py`.

## 4 الميزات

المسار الحي (`DeepFakeDetector`):

- صورة: تحسين، كشف وجوه بـ MTCNN عبر `ImageProcessor`، تحليل منطقة الوجه بـ Xception، تحليل جنائي للمنطقة، بيانات وصفية، جودة الصورة، ثم إضاءة.
- إن لم يُكتشف وجه تُحلَّل الصورة كاملة عبر `_analyze_full_image`.
- فيديو: استخراج حتى 30 إطاراً، تحليل كل إطار، اتساق زمني، رمش عبر `EyeBlinkingAnalyzer` حتى 50 إطاراً، إضاءة حتى 30 إطاراً.
- الصوت: الدرجة الافتراضية `real_score` 0.7 إذا لم يوجد ملف صوت. التحليل بـ `AudioAnalyzer` يعمل فقط عندما يكون ملف wav موجوداً مسبقاً بجانب الفيديو باسم يستبدل الامتداد بـ `_audio.wav`. المسار لا يستخرج المسار الصوتي من الفيديو داخل `analyze_video`.
- الناتج يُضغط للفيديو بين 0.1 و0.9.
- معاينة وصور تحليل تحت `static/analysis` حسب مفاتيح `artifacts`.
- مهمة غير متزامنة بخيط، والحالة في الذاكرة.

أوزان الدمج المكتوبة في `DeepFakeDetector.model_weights`: xception 0.6، forensics 0.3، metadata 0.1. في `analyze_image` الدمج الظاهر لوجه واحد يستدعي `_combine_scores` على أربع قيم: Xception والجنائيات والبيانات الوصفية وجودة الصورة. راجع الدالة `_combine_scores` عند تفسير الوزن الفعلي.

`XceptionDetector._calibrate_prediction` يعدّل الدرجة حسب التباين والحدة والسطوع (عتبات 30 و100 و10 و20 و235) ثم يحصر الناتج بين 0.1 و0.9. هذا تعديل قواعدي فوق مخرج الشبكة، والرأس الكثيف يُنشأ بأوزان ابتدائية لأنه لا يُحمَّل ملف `.h5` في البناء الافتراضي.

ملفات موجودة وغير موصولة بـ `upload-image`:

- `advanced_models.py` و`advanced_ml.py` (نماذج وبُنى تدريب فارغة أو أصناف تعلم غير مستدعاة من API).
- `websocket_handler.py`.
- `security_manager.py` (تشفير ملف، بصمة، فحص أنماط، حد معدل، تنظيف).
- `external_services.py` و`additional_features.py` (PDF، دفعة، بث، بريد).
- `performance_optimizer.py` في الجذر ونسخة داخل `app/utils`.

`forensics.py` يبحث في بيانات البرنامج عن كلمات مثل photoshop وgimp وكلمتي deepfake وface swap كإشارة تحرير في الميتاداتا. هذا فحص اسم برنامج داخل EXIF، وليس مولّد وسائط.

`advanced_forensics.py` يبحث عن أنماط تردد تُوصف في التعليق بأنها شائعة في صور GAN. الملف أداة تحليل. مسار الرفع يستورد `forensics.py` لا هذا الملف، إلا إذا استُدعي من مكان آخر. `DeepFakeDetector` يستورد `ForensicAnalyzer` من `app.utils.forensics`.

## 5 سير العمل

```
run.py -> create_app
GET /  -> index.html
POST /api/upload-image أو upload-video
  -> job_id في الذاكرة status=processing
  -> خيط DeepFakeDetector
GET /api/status/<job_id>
GET /api/result/<job_id>
GET /result/<job_id>  صفحة العرض
```

إعادة تشغيل العملية تمسح `job_results` لأن التخزين قاموس في الذاكرة. تعليق الكود يقول إن الإنتاج يحتاج Redis أو قاعدة. غير موجود في الملفات الحالية.

## 6 أمثلة واقعية

مستخدم يرفع صورة وجه PNG. المهمة ترجع `id` وحالة `processing` ثم `done`. الملخص فيه `real_score` و`fake_score` ومجموعها المنطقي قريب من 1، مع `explanations` وعدد الوجوه. إن فشل التحليل ترجع الدرجة 0.5 مع شرح من نوع `error`.

مستخدم يرفع MP4. يُسحب حتى 30 إطاراً. إن تباين درجات الإطارات أكبر من 0.1 تُنقص الدرجة المتوسطة بمقدار 0.2 قبل المزج. المزج النهائي: 0.4 للإطارات، 0.2 للاتساق الزمني، 0.2 للرمش، 0.1 للإضاءة، 0.1 للصوت.

عينات `sample_images` و`sample_videos` مجلدات مع `README.txt` بداخلها. لا قائمة ملفات وسائط في بحث الامتدادات الذي أُجري على المستودع.

## 7 رحلة المستخدم

1. `python run.py` بعد تثبيت المتطلبات.
2. فتح `http://127.0.0.1:5000`.
3. اختيار صورة أو فيديو من الواجهة (`main.js`).
4. انتظار الحالة.
5. فتح صفحة النتيجة وقراءة الدرجة والشروحات.
6. المعاينة من مسارات `artifacts` تحت الملفات الثابتة.

لا حساب يُنشأ.

## 8 الوحدات

| المسار | في المسار الحي؟ | الوظيفة |
| --- | --- | --- |
| `run.py` | نعم | فحص المكتبات وتشغيل Flask |
| `config.py` | نعم | حدود وأحجام |
| `app/__init__.py` | نعم | تسجيل البلوبرنت |
| `app/routes.py` | نعم | صفحات وصحة وخطوط |
| `app/api.py` | نعم | رفع ونتيجة |
| `app/models/ensemble.py` | نعم | دمج التحليل |
| `app/models/xception_detector.py` | نعم | شبكة Xception |
| `app/utils/image_utils.py` | نعم | وجوه ومعالجة |
| `app/utils/video_utils.py` | نعم | إطارات |
| `app/utils/forensics.py` | نعم | ضوضاء وضغط وتردد وEXIF |
| `app/utils/eye_blinking_analyzer.py` | نعم للفيديو | رمش |
| `app/utils/lighting_analyzer.py` | نعم | إضاءة |
| `app/utils/audio_analyzer.py` | مشروط بوجود wav | طيف وصوت |
| `tools/download_weights.py` | يدوي | تنزيل ملفات أوزان |
| بقية `app/models` و`app/utils` و`websocket_handler.py` | لا من API الرفع | أصناف جاهزة أو فارغة |

## 9 الكيانات

لا قاعدة SQL. كيان المهمة في الذاكرة:

| الحقل | المعنى |
| --- | --- |
| id | UUID |
| status | processing أو done أو error |
| summary | real_score, fake_score, explanations, وأحياناً frame_level وface_count |
| artifacts | مسارات معاينة |
| advanced_analysis | إضاءة، وجوه، وللمقطع رمش وصوت |
| error | نص عند الفشل |

الملف المرفوع يبقى في `uploads/` حتى يحذفه شيء آخر. `FILE_CLEANUP_HOURS = 24` في الإعداد، وخدمة الحذف في `security_manager.py` غير مستدعاة من `run.py`.

## 10 الصلاحيات

غير موجود في الملفات الحالية على مسارات الرفع والنتيجة. أي عميل يصل إلى المنفذ يستطيع الرفع وقراءة `job_id` إن عرفه. صفحة النتيجة ترفض معرفاً أقصر من 10 محارف وتعرض القالب بكلمة invalid.

`RateLimiter` في `security_manager.py` غير موصول بـ `api.py`.

## 11 الأتمتة

- خيط تحليل لكل رفع حتى يرجع الرد سريعاً بمعرف المهمة.
- `check_dependencies` قبل الإقلاع ويوقف التشغيل إن غابت حزمة مطلوبة.
- تنزيل الأوزان يدوي: `python tools/download_weights.py` أو مع `--auto`.
- لا cron. تنظيف 24 ساعة غير شغّال من نقطة الدخول.

## 12 تأثير الوحدات على بعضها

- فشل بناء TensorFlow يمنع الإقلاع لأن `run.py` يشترطه.
- غياب `python-magic` يبدّل فحص النوع إلى الامتداد، مع تحذير مطبوع.
- غياب dlib يبقى اختيارياً. `requirements.txt` يعلّق سطر dlib بسبب التثبيت على Windows.
- أوزان `download_weights.py` لا تُمرَّر تلقائياً إلى `XceptionDetector()` في `ensemble.py`. تنزيل الملف وحده لا يغيّر البناء الحالي.
- رأس التصنيف غير المدرَّب يجعل `raw_score` غير مرتبط بمجموعة تزوير، ثم المعايرة القواعدية تحرّك الدرجة داخل [0.1, 0.9].
- خطأ التحليل لا يوقف الخادم. المهمة تصبح `error` أو درجة 0.5 حسب طبقة الالتقاط.

## 13 مسرد

| المصطلح | في هذا الكود |
| --- | --- |
| real_score | تقدير أن اللقطة أقرب إلى حقيقية، بين 0 و1 وبعد الحصر غالباً 0.1 إلى 0.9 |
| fake_score | 1 ناقص real_score في ملخص الصورة والفيديو |
| Xception | عمود ImageNet مع رأس Dense جديد |
| Forensics | ضوضاء، ضغط، تردد، EXIF، اتساق لون، وإشارة إخفاء بيانات في `forensics.py` |
| job_id | معرف المهمة في الذاكرة |
| GAN patterns | تعليق فحص تردد في `advanced_forensics.py`، وليس مولّد صور |

## 14 أسئلة شائعة

**هل النظام يصنع فيديو مزوراً؟** لا. واجهة الرفع تستدعي التحليل فقط. دوال التدريب في `advanced_models.py` فارغة بـ `pass`.

**هل النسبة المئوية دليل جنائي؟** لا. الرأس غير مدرَّب على بيانات تزوير في المسار الافتراضي، والمعايرة قواعد سطوع وتباين. README السابق يذكر دقة عالية. تعليق `xception_detector.py` يقول إن الدقة الأفضل تحتاج تدريباً على بيانات DeepFake. المصدران مختلفان، وسلوك التشغيل يتبع التعليق والكود.

**لماذا تبقى الدرجة بعيدة عن 0 وعن 1؟** الحصر `max(0.1, min(0.9, ...))` في المعايرة وفي ملخص الفيديو.

**هل يُرسل ملفي للخارج؟** مسار الرفع المحلي لا يستدعي `external_services.py`. تلك الأصناف ترسل الصورة إذا استُدعيت ومعها مفتاح.

**أين تذهب المهام بعد الإيقاف؟** تُمسح مع العملية.

## 15 مخطط المعمارية ASCII

```
المتصفح index.html / result.html / main.js
        |
        v
Flask run.py
  main_bp     /   /result/<id>   /health   /assets/fonts
  api_bp      /api/upload-image|video   /api/status   /api/result
        |
        v
خيط: DeepFakeDetector
  Xception (ImageNet + رأس جديد)
  ForensicAnalyzer
  Eye / Lighting / Audio (wav جاهز)
        |
        +-- uploads/
        +-- static/analysis/
        +-- job_results (ذاكرة)

download_weights.py --> weights/   (غير موصول تلقائياً بالكشف)
advanced_*.py security_manager websocket external_services
        (موجودة وغير مستدعاة من api.py)
```

## 16 التقنيات المستخدمة

- Flask 2.2.5
- TensorFlow 2.12.1 وKeras 2.12.0
- OpenCV 4.8.1.78 وPillow 10.0.0 وMTCNN 1.0.0
- scikit-image وscikit-learn وnumpy وscipy
- librosa وsoundfile لتحليل الصوت عند استدعائه
- flask-socketio في المتطلبات، وغير مُشغَّل من `run.py`
- gunicorn في المتطلبات بلا Procfile
- HTML وCSS وJavaScript

`requirements.txt` يكرر حزماً بإصدارات مختلفة (scipy 1.10.1 ثم 1.11.1، وlibrosa وmatplotlib وseaborn وscikit-learn وjoblib أكثر من مرة). المثبت الأخير عند استخدام pip يعتمد على سلوك أداة التثبيت. الملف نفسه يحتوي التعارض.

## 17 شجرة الملفات

```
DeepFake/
├── run.py
├── config.py
├── performance_optimizer.py
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── api.py
│   ├── websocket_handler.py
│   ├── models/
│   │   ├── ensemble.py
│   │   ├── xception_detector.py
│   │   ├── advanced_models.py
│   │   └── advanced_ml.py
│   ├── utils/   image video forensics eye lighting audio
│   │            advanced_forensics external_services
│   │            security_manager additional_features
│   │            performance_optimizer
│   ├── templates/index.html result.html
│   └── static/css/main.css  js/main.js
├── tools/download_weights.py
├── weights/          (يُنشأ)
├── uploads/          (يُنشأ)
├── sample_images/README.txt
├── sample_videos/README.txt
└── assets/fonts/
```

## 18 الواجهة الأمامية

`index.html` رفع. `result.html` تعرض `job_id`. `main.js` يرسل النموذج ويستعلم الحالة. `main.css` التنسيق. README السابق يذكر وضعاً داكناً. تحقق من `main.css` عند تعديل الألوان. الخطوط تُقدَّم من `/assets/fonts/<filename>` انطلاقاً من مجلد `assets/fonts` في جذر المشروع.

## 19 الواجهة الخلفية

لا FastAPI.

`routes.py`: `index`, `result`, `health_check`, `serve_fonts`.

`api.py`: `_sanitize_for_json`, `_run_image_analysis`, `_run_video_analysis`, `allowed_file`, `get_file_type`, `upload_image`, `upload_video`, `get_result`, `get_status`.

`ensemble.py`: `analyze_image`, `analyze_video`, `analyze_image_frame`, `_combine_scores`, `_analyze_temporal_consistency`, شروحات، صناعة معاينات، `_analyze_full_image`, `_analyze_image_quality`.

`xception_detector.py`: `_build_model`, `preprocess_image`, `predict`, `_calibrate_prediction`, `analyze_face_region`.

`run.py`: `check_dependencies`, `main`.

## 20 تدفق الطلب

1. `POST` متعدد الأجزاء بحقل `file`.
2. فحص الامتداد: صور png jpg jpeg gif bmp tiff، وفيديو mp4 avi mov mkv wmv flv webm.
3. حفظ باسم آمن تحت `uploads`.
4. إنشاء UUID وحالة processing.
5. خيط يستدعي الكاشف.
6. `GET /api/status/<job_id>` أو `/api/result/<job_id>` يقرأ القاموس بعد تحويل أنواع numpy إلى JSON.

معاملات README السابق `max_frames` و`sample_rate` و`forensics_only` مذكورة هناك. توقيع `upload_image` في الملف يقرأ الملف. استخراج الإطارات داخل `analyze_video` يثبت `max_frames=30` في الاستدعاء، ولا يمرر تلك الحقول من النموذج إلى الكاشف في المقطع المقروء من `_run_video_analysis`. إن أرسلها العميل تُتجاهل في هذا المسار. هذا تناقض بين README السابق و`api.py`.

## 21 قاعدة البيانات

غير موجود في الملفات الحالية. المهام في الذاكرة. لا SQLite.

## 22 نقاط النهاية

| الطريقة | المسار | الغرض | المعاملات | مصادقة | الرد |
| --- | --- | --- | --- | --- | --- |
| GET | `/` | صفحة الرفع | - | لا | HTML |
| GET | `/result/<job_id>` | صفحة نتيجة | job_id | لا | HTML |
| GET | `/health` | صحة | - | لا | JSON status healthy |
| GET | `/assets/fonts/<filename>` | خط | filename | لا | ملف |
| POST | `/api/upload-image` | تحليل صورة | file | لا | JSON id, status processing |
| POST | `/api/upload-video` | تحليل فيديو | file | لا | JSON id, status processing |
| GET | `/api/status/<job_id>` | الحالة | job_id | لا | JSON status |
| GET | `/api/result/<job_id>` | النتيجة | job_id | لا | JSON summary وartifacts |

حد الحجم من الإعداد الافتراضي 500 ميجابايت. صنف الإنتاج في `config.py` يخفضه إلى 100 ميجابايت و`DEFAULT_MAX_FRAMES` إلى 20، وهذا الصنف يُحمَّل إذا كانت `FLASK_CONFIG=production`. `analyze_video` ما زال يمرر 30 يدوياً.

## 23 المصادقة

غير موجود في الملفات الحالية على واجهة الكشف.

## 24 الأمان الموجود فعلياً في الكود

- `secure_filename` عند الحفظ.
- فحص امتداد، و`python-magic` إن ثُبّت.
- حد حجم الجسم.
- `SECRET_KEY` من البيئة أو قيمة ثابتة في `config.py` (غير مطبوعة).
- معرف النتيجة يُرفض في الصفحة إن كان أقصر من 10 محارف، وAPI النتيجة يبحث في القاموس بلا هذا الفحص الإضافي necessarily بنفس الطريقة.
- لا جلسة ولا عزل بين مستخدمين.
- `job_id` من يعرفه يقرأ النتيجة.
- أصناف `security_manager.py` (Fernet، بصمة SHA، أنماط ملف، حد 60 طلباً في الدقيقة، إخفاء وجه، حذف ميتاداتا) غير موصولة بنقطة الدخول.
- وضع التصحيح يتبع صنف الإعداد. الافتراضي `DevelopmentConfig` و`DEBUG = True`.
- المضيف الافتراضي `127.0.0.1`.

## 25 مفاتيح الإعداد بدون قيم

لا `.env` في الشجرة.

| المفتاح | الأثر |
| --- | --- |
| FLASK_CONFIG | development أو production أو testing أو default |
| FLASK_HOST | افتراضي 127.0.0.1 |
| FLASK_PORT | افتراضي 5000 |
| FLASK_DEBUG | README السابق يذكره. `run.py` يأخذ `debug` من صنف الإعداد `DEBUG` لا من هذا المتغير في المقطع المقروء |
| SECRET_KEY | جلسة Flask إن استُخدمت |
| TF_CPP_MIN_LOG_LEVEL | يُضبط إلى 2 داخل `run.py` |
| GOOGLE_CLOUD_API_KEY | خدمة الرؤية، غير مستدعاة من الرفع |
| AWS_ACCESS_KEY_ID | عميل في external_services |
| AWS_SECRET_ACCESS_KEY | نفسه |
| AZURE_SUBSCRIPTION_KEY | نفسه |
| AZURE_ENDPOINT | نفسه |
| TELEGRAM_BOT_TOKEN | إشعار |
| SMTP_SERVER | افتراضي smtp.gmail.com |
| SMTP_PORT | افتراضي 587 |
| EMAIL_USERNAME | بريد |
| EMAIL_PASSWORD | سر البريد |

تناقض: README السابق يقول إن `FLASK_DEBUG` يفعّل التطوير. `run.py` يقرأ `FLASK_CONFIG` ثم `app_config.DEBUG`.

## 26 التكاملات

المستدعاة من الكشف: TensorFlow/Keras، OpenCV، MTCNN، Pillow.

اختيارية وغير موصولة بالرفع: Google Vision، AWS، Azure، Telegram، SMTP، كما في `external_services.py`.

`download_weights.py` يطلب ملفات من عناوين dlib وGitHub (أوزان Xception العامة من مستودع Keras، وملفات بأسماء deepfake من مسار FaceForensics). بعض قيم MD5 في الملف سلاسل متكررة الشكل مثل أنماط `a1b2c3`، ففشل التحقق محتمل لأن القيمة ليست بصمة منشورة حقيقية. الأداة لا تغيّر مسار `XceptionDetector()` الحالي حتى لو نجح التنزيل.

## 27 المهام المجدولة

غير موجود في الملفات الحالية كعملية تعمل مع الخادم. ثابت 24 ساعة بلا مستدعٍ من `run.py`.

## 28 تخزين الملفات

`uploads/` للمدخلات. `static/analysis/` للمعاينات. `weights/` للأوزان المنزّلة. تُنشأ المجلدات في `Config.init_app` أو في `create_app`.

## 29 التسجيل

`print` في `run.py` والكواشف. لا جدول تدقيق. `security_manager.log_access` غير موصول.

## 30 التثبيت من requirements

```
pip install -r requirements.txt
python run.py
```

تنزيل أوزان اختياري وغير كافٍ وحده لتبديل رأس الشبكة:

```
python tools/download_weights.py
```

Python حسب README السابق: 3.10.6. الذاكرة الموصى بها هناك 8 جيجابايت و4 كحد أدنى، والمساحة 2 جيجابايت. لا ملف يفرض ذلك آلياً.

الحزم الثقيلة (TensorFlow) لازمة لأن `check_dependencies` يوقف الإقلاع بدونها.

## 31 دليل التطوير

- عدّل الكشف في `ensemble.py` لا في أصناف غير مستدعاة إن أردت تغييراً يراه المستخدم.
- لتمرير أوزان مدرَّبة فعلياً على الكشف، مرّر `weights_path` إلى `XceptionDetector` من `DeepFakeDetector.__init__`. هذا غير موجود اليوم.
- لا تضف مسار توليد وسائط. نطاق المشروع الحالي التحليل.
- وحّد تكرار الإصدارات في `requirements.txt` يدوياً لاحقاً. هذا الملف لم يُغيَّر مع التوثيق.
- المهام في الذاكرة غير صالحة لأكثر من عملية gunicorn واحدة.

## 32 النشر

غير موجود في الملفات الحالية: Procfile أو دليل Heroku.

`run.py` يطبع مثالاً: `gunicorn -w 4 run:app`. حزمة gunicorn موجودة في المتطلبات. عدة عمليات عامل تعني ذاكرة مهام منفصلة لكل عملية، فمعرف المهمة قد لا يُوجد عند العامل الذي يستلم طلب النتيجة. هذا قيد للتعليمة المطبوعة.

الإنتاج في الكود: `FLASK_CONFIG=production` يخفض حد الرفع إلى 100 ميجابايت ويطفئ DEBUG على الصنف.

## 33 النسخ الاحتياطي

لا قاعدة. انسخ `uploads/` و`static/analysis/` و`weights/` إن كانت الملفات مهمة. مهام التحليل تُفقد عند الإيقاف حتى مع بقاء الملفات.

## 34 استكشاف الأخطاء

| العرض | السبب في الكود |
| --- | --- |
| خروج فوري | مكتبة من `check_dependencies` ناقصة |
| تحذير magic | libmagic غير مثبت، والفحص بالامتداد |
| درجة قرب 0.5 | فشل تحليل أو رأس غير مدرَّب مع معايرة |
| 404 على النتيجة بعد إعادة التشغيل | القاموس في الذاكرة |
| الصوت دائماً 0.7 | لا ملف `_audio.wav` جاهز |
| الأوزان المنزّلة بلا أثر | `XceptionDetector()` بلا مسار |
| المنفذ | `FLASK_PORT` |

## 35 الاعتماديات مع الإصدارات من requirements.txt

القائمة كما في الملف، بما فيها التكرار:

| الحزمة | الإصدار المذكور |
| --- | --- |
| Flask | 2.2.5 |
| Werkzeug | 2.2.3 |
| numpy | 1.23.5 |
| pandas | 2.0.3 |
| scipy | 1.10.1 ثم 1.11.1 مكرر |
| opencv-python | 4.8.1.78 |
| Pillow | 10.0.0 |
| scikit-image | 0.24.0 |
| imutils | 0.5.4 |
| imageio | 2.37.0 |
| tensorflow | 2.12.1 |
| tensorflow-intel | 2.12.1 |
| tensorflow-estimator | 2.12.0 |
| tensorboard | 2.12.3 |
| keras | 2.12.0 |
| scikit-learn | 1.3.0 مكرر |
| mtcnn | 1.0.0 |
| tqdm | 4.66.1 |
| python-magic | 0.4.27 |
| aiofiles | 24.1.0 |
| gunicorn | 21.2.0 |
| psutil | 7.0.0 |
| matplotlib | 3.7.2 مكرر |
| seaborn | 0.12.2 مكرر |
| Jinja2 | 3.1.2 |
| MarkupSafe | 3.0.2 |
| itsdangerous | 2.2.0 |
| click | 8.2.1 |
| blinker | 1.9.0 |
| joblib | 1.5.1 مكرر |
| threadpoolctl | 3.6.0 |
| requests | 2.31.0 |
| urllib3 | 2.0.7 |
| certifi | 2025.7.14 |
| charset-normalizer | 3.4.2 |
| idna | 3.7 |
| sympy | 1.14.0 |
| mpmath | 1.3.0 |
| librosa | 0.10.1 مكرر |
| flask-socketio | 5.3.6 |
| eventlet | 0.33.3 |
| reportlab | 4.0.4 |
| soundfile | 0.12.1 |
| cryptography | 41.0.4 |
| secure-smtplib | 0.1.1 |
| albumentations | 1.3.1 |

سطر `dlib==19.24.2` معلّق كاختياري بسبب Windows.

## 36 القيود

- الكشف الافتراضي ليس نموذجاً مُدرَّباً على بيانات تزوير.
- الدرجة محصورة بعيداً عن القطبين.
- الصوت لا يُستخرج من الفيديو داخل الدالة.
- النتائج في الذاكرة وبلا مصادقة.
- معاملات الإطارات في README السابق غير موصولة بالرفع.
- أدوات الأمان والخدمات الخارجية والويب سوكت غير داخلة في مسار الطلب.
- تدريب FaceForensics في `advanced_models.py` غير منفَّذ.
- تعارض إصدارات داخل `requirements.txt`.
- غير مناسب كدليل وحيد على أصالة وسيط.

## 37 الحالة الحالية

خادم كشف محلي يعمل إذا توفرت مكتبات الرؤية وTensorFlow. الواجهة ترفع ملفاً وتعرض درجة وشروحاً. كثير من الملفات المتقدمة هيكل بلا استدعاء من API. لا توليد وسائط في المسارات.

## 38 قرارات المعمارية

- دمج قواعد وجنائيات مع شبكة عامة لأن ملف أوزان الكشف غير مربوط.
- تحليل في خيط حتى لا ينتظر المتصفح بناء النموذج داخل الطلب نفسه. كل مهمة تنشئ `DeepFakeDetector()` من جديد، فيُبنى النموذج لكل رفع.
- ذاكرة عملية بدل قاعدة، كما يقول التعليق، مع الإشارة إلى Redis لاحقاً.
- حصر الدرجات لتفادي 0 و1 من معايرة سطحية.
- الإبقاء على أصناف متقدمة في الشجرة دون تفعيلها من `api.py`.

## 39 سجل التغييرات

غير موثق. لا رقم إصدار تطبيق في `config.py`.

## System Overview

موقع محلي يرفع صورة أو فيديو ويقدّر درجة واقعية بمزيج من شبكة Xception بأوزان ImageNet ورأس غير مدرَّب، وفحوص ضوضاء وبيانات وصفية وإضاءة، وللفيديو رمش واتساق إطارات. الناتج شرح للمستخدم وليس تقريراً قضائياً. النظام لا ينشئ وسائط مزورة من هذه المسارات.

## Quick Reference

| البند | القيمة |
| --- | --- |
| تشغيل | `python run.py` |
| العنوان | `http://127.0.0.1:5000` |
| صحة | `GET /health` |
| رفع | `POST /api/upload-image` أو `upload-video` |
| صور | png jpg jpeg gif bmp tiff |
| فيديو | mp4 avi mov mkv wmv flv webm |
| حد افتراضي | 500 ميجابايت |
| إطارات الفيديو في الكود | 30 |
| تخزين المهام | ذاكرة العملية |
| حسابات | لا يوجد |

## Quick Start

```
pip install -r requirements.txt
python run.py
```

افتح الصفحة، ارفع صورة اختبار تملك حق استخدامها، وانتظر الحالة ثم افتح النتيجة. الدرجة تقدير داخلي لهذا البناء.

## For Non-Technical Users

الموقع يفحص صورة أو فيديو عندك ويعرض رقماً يميل إلى «أقرب إلى حقيقي» أو «أقرب إلى متلاعب به»، مع جمل تشرح ما لاحظه البرنامج (وجه، إضاءة، جودة). الرقم ليس حكماً نهائياً من جهة رسمية. أعد تشغيل البرنامج يمسح نتائج الفحص السابقة من الذاكرة حتى لو بقي الملف على القرص. لا تستخدم النتيجة لاتهام شخص. البرنامج هنا للفحص فقط.

## For Developers

المسار الذي يراه المستخدم: `run.py` ثم `api.py` ثم `ensemble.py`. أصناف `advanced_models.py` فارغة عند التدريب. وصّل `weights_path` فقط عندما تملك ملف أوزان كشف حقيقياً وتتحقق من مصدره. لا تبنِ من هذا المستودع مسار توليد. أصلح تعارض scipy في المتطلبات قبل نشر ثابت. عدة عمال gunicorn لا تشارك `job_results`.
