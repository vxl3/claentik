# 🚀 دليل النشر (Deployment Guide)

هذا الدليل يشرح **ثلاث طرق** لتشغيل البوت، من الأسهل إلى الأكمل، حتى تختار
الأنسب حسب توفر الرصيد عندك.

---

## ⚠️ معلومة أساسية قبل أي شيء

البوت فيه جزآن من ناحية المتطلبات:

| الجزء | الذاكرة المطلوبة | الوصف |
|---|---|---|
| **البوت الأساسي** | ~100-200MB | القوائم، إدارة الحسابات، قاعدة البيانات، لوحة الإدارة، الإحصائيات |
| **أتمتة TikTok** | ~500MB - 1GB | متصفح Chromium المستخدم لتسجيل الدخول وتنفيذ التنظيف |

**قاعدة ذهبية:**
- أي استضافة مجانية (512MB) → تشغّل **البوت الأساسي فقط** (بدون أتمتة TikTok).
- أتمتة TikTok الكاملة → تحتاج **Oracle Cloud المجاني (24GB)** أو **VPS (2GB+)**.

---

## 📊 جدول مقارنة سريع

| المسار | التكلفة | يعمل 24/7؟ | أتمتة TikTok؟ | الصعوبة |
|---|---|---|---|---|
| **1. Koyeb** | مجاني | ✅ | ❌ | سهلة |
| **2. Oracle Cloud** | مجاني (يحتاج بطاقة للتحقق) | ✅ | ✅ كاملة | متوسطة |
| **3. VPS** | ~$5/شهر | ✅ | ✅ كاملة | متوسطة |

---

# المسار 1️⃣ — Koyeb (مجاني، بوت أساسي 24/7، بدون أتمتة TikTok)

> مناسب إذا تريد البوت يشتغل دائمًا الآن مجانًا (قوائم + حسابات + إحصائيات +
> لوحة إدارة)، بدون عمليات تنظيف TikTok الفعلية.

### الخطوات:

1. افتح [koyeb.com](https://www.koyeb.com) وسجّل حسابًا (بريد + كلمة مرور، بدون بطاقة عادةً).

2. بعد التسجيل، اضغط **Create Service** ← **Deploy from GitHub**.

3. اربط حساب GitHub الخاص بك واختر المستودع `vxl3/claentik`.

4. في إعدادات الخدمة:
   - **Name**: `cleantik-bot`
   - **Builder**: `Dockerfile`
   - **Port**: لا حاجة (البوت يستخدم Long Polling وليس webhook)

5. أضف **Environment Variables** (من تبويب Advanced):

   ```
   TELEGRAM_BOT_TOKEN=رمز_البوت_الخاص_بك
   OWNER_TELEGRAM_ID=رقم_حسابك
   DATABASE_URL=sqlite+aiosqlite:///./tiktokbot.db
   LOG_LEVEL=INFO
   LOG_DIR=logs
   TIKTOK_AUTOMATION_ENABLED=true
   TIKTOK_BROWSER_HEADLESS=true
   TIKTOK_PERSIST_SESSION=false
   ```

6. اضغط **Deploy** وانتظر 2-4 دقائق.

7. بعد النشر، افتح بوتك في Telegram وأرسل `/start`.

> ⚠️ **ملاحظة:** Koyeb المجاني يعطي ~512MB ذاكرة فقط، لذا عند الضغط على
> "إضافة حساب" سترى رسالة واضحة: "أتمتة TikTok غير متاحة على هذا الخادم".
> كل شيء آخر يعمل بشكل كامل.

> 💡 **نقطة مهمة عن قاعدة البيانات:** Koyeb يعيد تشغيل الحاوية أحيانًا ويفقد
> الملفات المؤقتة (لأن SQLite ملف محلي). لو أردت بيانات دائمة، استخدم
> PostgreSQL خارجي (مثل Neon المجاني) واضبط `DATABASE_URL` عليه.

---

# المسار 2️⃣ — Oracle Cloud Free Tier (مجاني للأبد، 24GB، أتمتة كاملة) ⭐

> **هذا هو الحل الأقوى والأمثل** — سيرفر كامل 24GB ذاكرة **مجاني للأبد**،
> يشغّل البوت **كاملًا بأتمتة TikTok** بدون أي تكلفة شهرية.
>
> **الشرط الوحيد:** بطاقة بنكية للتحقق من الهوية (لا يخصم منها شيئًا — فقط
> "حجز مؤقت" ~$1 يرجعه فورًا). لهذا تحتاج بطاقة فيها ولو رصيد رمزي.

### الخطوات (مفصلة):

#### أ) إنشاء السيرفر المجاني

1. افتح [signup.oraclecloud.com](https://signup.oraclecloud.com).
2. سجّل حسابًا ببريدك وأدخل بيانات بطاقتك (للتحقق فقط).
3. بعد التسجيل، من القائمة اختر **Compute → Instances → Create Instance**.
4. اختر:
   - **Name**: `cleantik`
   - **Image**: Ubuntu 22.04 (أو 24.04)
   - **Shape**: `VM.Standard.A1.Flex` مع **4 OCPUs و 24GB RAM** (Arm — مجاني ضمن Always Free).
   - **SSH Key**: حمّل مفتاح SSH (أو ولّد واحدًا).
5. اضغط **Create** وانتظر دقيقة.

#### ب) الاتصال بالسيرفر

```bash
# من كمبيوترك أو من تطبيق Termius على الجوال:
ssh -i cleantik.key ubuntu@IP_السيرفر
```

#### ج) تثبيت كل شيء (انسخ والصق هذا السكريبت كاملًا):

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git

# استنساخ المشروع
git clone https://github.com/vxl3/claentik.git
cd claentik

# بيئة Python معزولة
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install --with-deps chromium

# إنشاء ملف الإعدادات (عدّل القيم)
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=رمز_البوت_الخاص_بك
OWNER_TELEGRAM_ID=رقم_حسابك
DATABASE_URL=sqlite+aiosqlite:///./tiktokbot.db
LOG_LEVEL=INFO
LOG_DIR=logs
TIKTOK_AUTOMATION_ENABLED=true
TIKTOK_BROWSER_HEADLESS=true
TIKTOK_PERSIST_SESSION=false
EOF
```

#### د) التشغيل الدائم عبر systemd

```bash
# أنشئ ملف الخدمة
sudo tee /etc/systemd/system/cleantik.service > /dev/null << 'EOF'
[Unit]
Description=CleanTik Telegram Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/claentik
EnvironmentFile=/home/ubuntu/claentik/.env
ExecStart=/home/ubuntu/claentik/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# فعّل الخدمة
sudo systemctl daemon-reload
sudo systemctl enable --now cleantik
sudo systemctl status cleantik
```

> البوت الآن يعمل **24/7 مجانًا للأبد** مع **أتمتة TikTok الكاملة**.

#### هـ) سجلّات التشغيل

```bash
journalctl -u cleantik -f          # متابعة السجلات لحظيًا
journalctl -u cleantik --since today
```

---

# المسار 3️⃣ — VPS رخيص (~$5 شهريًا، أتمتة كاملة)

> نفس خطوات Oracle تمامًا، لكن على VPS من:
> - **Hostinger** (الأسهل للمبتدئ)
> - **Contabo** (أرخص ومواصفات أعلى: 4GB بـ ~$5)
>
> عند الشراء اختر نظام **Ubuntu 22.04 أو 24.04**، وذاكرة **2GB على الأقل**.
>
> ثم اتبع **نفس الأوامر في المسار 2** (من "الاستنساخ" حتى systemd).

---

## 🔧 استكشاف الأخطاء الشائعة

| المشكلة | الحل |
|---|---|
| البوت لا يرد | تحقق من `TELEGRAM_BOT_TOKEN` ومن أن الخدمة تعمل (`systemctl status`) |
| "أتمتة TikTok غير متاحة" | هذا يعني الخادم بلا Chromium — تأكد من `playwright install --with-deps chromium` |
| TikTok يرفض الدخول / CAPTCHA | لا نتجاوزها أبدًا؛ جرّب الدخول عبر QR من عنوان IP مختلف أو لاحقًا |
| قاعدة البيانات تختفي بعد إعادة التشغيل (Koyeb) | استخدم PostgreSQL خارجي (Neon) |

---

## 🔐 ملاحظات أمنية أخيرة

1. **لا ترفع `.env` إلى GitHub أبدًا** (مستثنى تلقائيًا عبر `.gitignore`).
2. **احذف/أبطل أي Token شاركته** في محادثات بعد الانتهاء من استخدامه.
3. **الأتمتة غير رسمية** وتخالف شروط TikTok — استخدمها بحذر وعلى حسابك أنت فقط.
4. الفواصل الزمنية محافظة افتراضيًا، ولا تتجاوز أنظمة حماية TikTok.

---

**الأفضل لك: المسار 2 (Oracle Cloud) — مجاني للأبد + أتمتة كاملة.**
كل ما تحتاجه هو بطاقة فيها ولو رصيد رمزي ($1) للتسجيل فقط.
