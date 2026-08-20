#!/usr/bin/env bash
# ============================================================
#  سكريبت نشر تلقائي لسيرفر Ubuntu (Oracle Cloud / VPS)
#
#  يشغّل البوت كاملًا (مع أتمتة TikTok) ويجعله خدمة systemd دائمة.
#
#  الاستخدام (على السيرفر مباشرة):
#    chmod +x scripts/deploy_vps.sh
#    sudo TELEGRAM_BOT_TOKEN=xxx OWNER_TELEGRAM_ID=123 ./scripts/deploy_vps.sh
# ============================================================
set -euo pipefail

# --- المتغيرات المطلوبة ---
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
OWNER_TELEGRAM_ID="${OWNER_TELEGRAM_ID:-}"

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$OWNER_TELEGRAM_ID" ]; then
    echo "خطأ: عرّف المتغيرين أولًا:"
    echo "  export TELEGRAM_BOT_TOKEN=رمز_البوت"
    echo "  export OWNER_TELEGRAM_ID=رقمك"
    exit 1
fi

REPO_URL="https://github.com/vxl3/claentik.git"
INSTALL_DIR="/opt/claentik"
SERVICE_NAME="cleantik"

echo "=== 1) تثبيت الحزم الأساسية ==="
apt update -y
apt install -y python3 python3-pip python3-venv git

echo "=== 2) استنساخ المشروع ==="
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    git pull
else
    git clone "$REPO_URL" "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

echo "=== 3) إنشاء بيئة Python ==="
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "=== 4) تثبيت Chromium لـ Playwright ==="
playwright install --with-deps chromium

echo "=== 5) إنشاء ملف .env ==="
cat > .env << EOF
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
OWNER_TELEGRAM_ID=${OWNER_TELEGRAM_ID}
DATABASE_URL=sqlite+aiosqlite:///./tiktokbot.db
LOG_LEVEL=INFO
LOG_DIR=logs
TIKTOK_AUTOMATION_ENABLED=true
TIKTOK_BROWSER_HEADLESS=true
TIKTOK_PERSIST_SESSION=false
EOF
chmod 600 .env

echo "=== 6) إنشاء خدمة systemd ==="
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=CleanTik Telegram Bot
After=network.target

[Service]
User=root
WorkingDirectory=${INSTALL_DIR}
EnvironmentFile=${INSTALL_DIR}/.env
ExecStart=${INSTALL_DIR}/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now ${SERVICE_NAME}

echo ""
echo "✅ تم النشر بنجاح!"
echo "   - الحالة:  systemctl status ${SERVICE_NAME}"
echo "   - السجلات: journalctl -u ${SERVICE_NAME} -f"
echo "   - افتح البوت في Telegram وأرسل /start"
