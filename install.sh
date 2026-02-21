#!/bin/bash

# Упрощенный скрипт установки systemd service
# Использование: sudo ./install.sh

set -e

PROJECT_NAME="clinic-bot"
PROJECT_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="clinicbot"
VENV_DIR="$PROJECT_DIR/venv"

echo "=== Установка systemd service для $PROJECT_NAME ==="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "Ошибка: Запустите скрипт с правами root (sudo ./install.sh)"
    exit 1
fi

# Проверка существования директории проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Ошибка: Директория проекта $PROJECT_DIR не найдена"
    echo "Сначала запустите deploy.sh для развертывания проекта"
    exit 1
fi

# Проверка существования пользователя
if ! id "$SERVICE_USER" &>/dev/null; then
    echo "Создание пользователя $SERVICE_USER..."
    useradd -r -s /bin/bash -d "$PROJECT_DIR" "$SERVICE_USER"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
fi

# Определение пути к Python
if command -v python3.12 &> /dev/null; then
    PYTHON_PATH="/usr/bin/python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_PATH="/usr/bin/python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_PATH="/usr/bin/python3.10"
else
    PYTHON_PATH="/usr/bin/python3"
fi

# Создание service файла
cat > "/etc/systemd/system/$PROJECT_NAME.service" << EOF
[Unit]
Description=ROYAL Clinic Telegram Bot
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PYTHON_PATH $PROJECT_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$PROJECT_NAME

# Ограничения ресурсов
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

echo "=== Service установлен! ==="
echo ""
echo "Команды для управления:"
echo "  Запуск:   sudo systemctl start $PROJECT_NAME"
echo "  Остановка: sudo systemctl stop $PROJECT_NAME"
echo "  Статус:   sudo systemctl status $PROJECT_NAME"
echo "  Логи:     sudo journalctl -u $PROJECT_NAME -f"
echo "  Автозапуск: sudo systemctl enable $PROJECT_NAME"
