# بوت إدارة حسابات TikTok — Production Ready

بوت Telegram عربي بالكامل يساعد المستخدم على تنظيم حسابه في TikTok: تسجيل الدخول،
مقارنة قائمة المتابعين والمتابَعين، وتنفيذ عمليات التنظيف (إلغاء متابعة / إزالة
متابعين) بشكل آلي متدرّج ومحافظ.

> ⚠️ **إفصاح مهم — قبل أي شيء:** لا توفّر TikTok أي API رسمي يسمح لطرف ثالث
> بقراءة قوائم المتابعين/المتابَعين أو تنفيذ عمليات إلغاء متابعة/حظر. لذلك يعتمد
> هذا المشروع على **أتمتة المتصفح (Playwright)** بجلسة تسجيل دخول المستخدم نفسه.
> هذا الأسلوب **غير رسمي ويخالف شروط استخدام TikTok** وقد يؤدي إلى تقييد الحساب أو
> حظره. البوت لا يتجاوز CAPTCHA ولا Rate Limits ولا أي نظام حماية، ويتوقف فورًا
> عند رصد أي تقييد.

---

## 1. وصف المشروع

- إدارة عدة حسابات TikTok لكل مستخدم.
- تسجيل دخول عبر **QR** (الأكثر أمانًا) أو **بريد/هاتف + كلمة مرور + OTP**.
- عمليتان منفصلتان:
  - 🧹 **تنظيف Following**: إلغاء متابعة من لا يتابعك.
  - 🗑️ **تنظيف Followers**: إزالة من يتابعك وأنت لا تتابعه (تتم عبر الحظر لأن
    TikTok لا يوفر "إزالة متابع" مباشرة).
- إحصائيات قبل التنفيذ وأثناءه ونتيجة نهائية.
- فواصل زمنية محافظة + Exponential Backoff، مع إيقاف آمن.
- نظام Owner/Admin مع لوحة إدارة و Broadcast وسجلات.
- لا تخزين دائم لكلمة المرور أو OTP أو الجلسة.

## 2. المميزات (Features)

- ✅ بوت عربي بالكامل (Inline Keyboard احترافية، Edit Message لتحديث التقدم).
- ✅ عدة حسابات TikTok معزولة بالكامل لكل مستخدم.
- ✅ تسجيل دخول QR + بديل بالبيانات + OTP (دون حفظ الأسرار).
- ✅ نظام عمليات خلفي (Background Jobs) بدون تجميد البوت.
- ✅ منع تشغيل عمليتين على نفس الحساب.
- ✅ زر ⛔ إيقاف العملية.
- ✅ إحصائيات Owner + Broadcast آمن ومتدرج.
- ✅ Setup Wizard تلقائي لإنشاء `.env`.
- ✅ PostgreSQL + SQLAlchemy 2.0 (async) + Alembic.
- ✅ Logging مع إخفاء الأسرار تلقائيًا.
- ✅ اختبارات (pytest) و Docker Deployment.

## 3. المتطلبات (Requirements)

- Python 3.11+
- PostgreSQL 14+
- (لأتمتة TikTok) متصفح Chromium عبر Playwright

## 4. التثبيت (Installation)

```bash
git clone <repo-url> tiktok-cleaner-bot
cd tiktok-cleaner-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 5. متغيرات البيئة (Environment Variables)

| المتغير | الوصف | مطلوب |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | رمز البوت من @BotFather | ✅ |
| `OWNER_TELEGRAM_ID` | معرّف المالك (Owner) | ✅ |
| `DATABASE_URL` | رابط PostgreSQL (بصيغة asyncpg) | ✅ |
| `LOG_LEVEL` / `LOG_DIR` | مستوى وسجلّات التسجيل | اختياري |
| `TIKTOK_AUTOMATION_ENABLED` | تفعيل أتمتة TikTok | اختياري |
| `TIKTOK_BROWSER_HEADLESS` | تشغيل المتصفح بدون واجهة | اختياري |
| `TIKTOK_PERSIST_SESSION` | حفظ الجلسة (false موصى به) | اختياري |
| `PACING_*` | إعدادات الفواصل الزمنية | اختياري |
| `BROADCAST_*` | إعدادات البث | اختياري |

انظر `.env.example` للقيم الكاملة.

## 6. إعداد قاعدة البيانات

```bash
# أنشئ قاعدة البيانات والمستخدم (مثال):
sudo -u postgres psql -c "CREATE USER tiktokbot WITH PASSWORD 'tiktokbot_password';"
sudo -u postgres psql -c "CREATE DATABASE tiktokbot OWNER tiktokbot;"

# شغّل الـ migrations:
alembic upgrade head
```

> ملاحظة: البوت يقوم تلقائيًا بإنشاء الجداول (idempotent `create_all`) عند بدء
> التشغيل كوسيلة راحة؛ استخدم Alembic لإدارة الإصدارات في الإنتاج.

## 7. إعداد بوت Telegram

1. تواصل مع [@BotFather](https://t.me/BotFather).
2. أنشئ بوتًا جديدًا واحصل على الـ Token.
3. ضع الـ Token في `.env` (أو عبر الـ Setup Wizard).

## 8. إعداد المالك (Owner)

- شغّل `python -m scripts.setup_wizard` وأدخل `OWNER_TELEGRAM_ID` (رقم حسابك).
- عند أول تشغيل يمنح البوت دور `OWNER` لهذا المعرّف تلقائيًا، وستظهر لك
  "⚙️ لوحة الإدارة" في القائمة الرئيسية.

## 9. تشغيل المشروع

```bash
# 1) إنشاء ملف .env (إن لم يكن موجودًا):
python -m scripts.setup_wizard

# 2) التثبيت:
pip install -r requirements.txt
playwright install chromium

# 3) الـ migrations:
alembic upgrade head

# 4) التشغيل:
python main.py
```

أوامر Telegram: `/start` `/help` `/settings` `/accounts` `/cancel`

## 10. النشر (Deployment)

### عبر Docker (موصى به)

```bash
# تأكد من وجود .env ثم:
docker compose up -d --build
```

يُشغّل هذا PostgreSQL + البوت معًا مع سياسة إعادة تشغيل `unless-stopped`.

### عبر Systemd (بدون Docker)

```ini
# /etc/systemd/system/tiktokbot.service
[Unit]
Description=TikTok Cleaner Bot
After=network.target postgresql.service

[Service]
User=deploy
WorkingDirectory=/opt/tiktok-cleaner-bot
EnvironmentFile=/opt/tiktok-cleaner-bot/.env
ExecStart=/opt/tiktok-cleaner-bot/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now tiktokbot
journalctl -u tiktokbot -f
```

## 11. استكشاف الأخطاء (Troubleshooting)

| المشكلة | الحل |
|---|---|
| `Configuration is incomplete` | شغّل `python -m scripts.setup_wizard` |
| لا يبدأ البوت | تحقق من صحة الـ Token واتصال الشبكة |
| فشل أتمتة TikTok | تأكد من `playwright install chromium` ومن أن الحساب ليس محظورًا |
| تعذر الاتصال بقاعدة البيانات | تحقق من `DATABASE_URL` ومن تشغيل PostgreSQL |
| TikTok يحدّ العمليات | هذا سلوك متوقع؛ البوت يتوقف بأمان — خفّض سرعة العمليات |

## 12. ملاحظات أمنية (Security Notes)

- لا تُخزَّن كلمات المرور أو OTP أو الجلسات بشكل دائم (افتراضيًا في الذاكرة فقط).
- لا تُسجَّل الأسرار في الـ Logs (يوجد Redaction تلقائي).
- الأسرار عبر Environment Variables فقط، و`.env` ضمن `.gitignore`.
- لا تثق بأي إدخال من المستخدم (Validation على كل المدخلات).
- لا تتجاوز حماية TikTok: أي رصد لتقييد/حظر يُوقف العملية فورًا.

## 13. الـ Architecture

```
Telegram (aiogram) → Handlers → Services → TikTok Adapter (Playwright)
                                            ↘
                                        Repositories → PostgreSQL
```

طبقات معزولة: الـ TikTok Adapter خلف واجهة (`TikTokClient`) قابلة للاستبدال،
وكل حساب له جلسة/سياق متصفح معزول، ونظام عمليات خلفي يمنع التزامن على نفس
الحساب مع فجوات زمنية محافظة.

هيكل المشروع:

```
app/
├── bot/            # dispatcher, middlewares, states, callbacks
├── handlers/       # start, login, accounts, operations, stats, settings, owner
├── keyboards/      # inline keyboards
├── services/       # business logic
├── tiktok/         # adapter (base, playwright_client, errors, models, ...)
├── database/       # engine, base
├── models/         # SQLAlchemy ORM models
├── repositories/   # data access
├── workers/        # operation manager, job, progress reporter
├── security/       # access, validation, temp_store
├── utils/          # logger, formatting, text
└── config/         # settings, pacing
migrations/         # Alembic
tests/              # pytest
scripts/            # setup wizard
```

## 14. الاختبار (Testing)

```bash
python -m pytest -q
```

تغطي الاختبارات: إنشاء المستخدم، إضافة/حذف الحسابات، عدة حسابات، مقارنة
Followers/Following، سجلات العمليات، الـ pacing/backoff، الصلاحيات، التحقق من
المدخلات، التخزين المؤقت، والـ Broadcast.

---

### الإفصاح الكامل حول قدرات TikTok (للمطور)

| الميزة | الحالة |
|---|---|
| البوت + DB + إدارة الحسابات + الإحصائيات + Owner + Broadcast | ✅ رسمي وآمن |
| قراءة Followers/Following | ⚠️ عبر أتمتة المتصفح فقط (غير رسمي) |
| إلغاء متابعة | ⚠️ عبر أتمتة المتصفح فقط (غير رسمي) |
| إزالة متابع | ⚠️ عبر الحظر (لا يوجد زر "إزالة" في TikTok) |
| تجاوز CAPTCHA / Rate Limits / الحماية | ❌ لن يُنفَّذ أبدًا |
