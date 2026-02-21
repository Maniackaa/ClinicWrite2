#!/bin/bash

# Скрипт развертывания Telegram бота ROYAL Clinic на сервере
# Использование: ./deploy.sh

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Переменные
PROJECT_NAME="clinic-bot"
PROJECT_DIR="/opt/$PROJECT_NAME"
SERVICE_USER="clinicbot"
# Определяем доступную версию Python (3.12+ предпочтительно, минимум 3.10+)
if command -v python3.12 &> /dev/null; then
    PYTHON_VERSION="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_VERSION="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON_VERSION="python3.10"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION="python3"
else
    PYTHON_VERSION="python3"
fi

echo -e "${GREEN}=== Развертывание Telegram бота 'Объединяем компетенции' ===${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo ./deploy.sh)${NC}"
    exit 1
fi

# Создание пользователя для бота (если не существует)
if ! id "$SERVICE_USER" &>/dev/null; then
    echo -e "${YELLOW}Создание пользователя $SERVICE_USER...${NC}"
    useradd -r -s /bin/bash -d "$PROJECT_DIR" "$SERVICE_USER"
    echo -e "${GREEN}Пользователь $SERVICE_USER создан${NC}"
else
    echo -e "${GREEN}Пользователь $SERVICE_USER уже существует${NC}"
fi

# Создание директории проекта
echo -e "${YELLOW}Создание директории проекта...${NC}"
mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/data/video"
mkdir -p "$PROJECT_DIR/data/photo"
chown -R "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"
chmod -R 775 "$PROJECT_DIR/logs"

# Копирование файлов проекта
echo -e "${YELLOW}Копирование файлов проекта...${NC}"
# Предполагается, что скрипт запускается из директории проекта
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/" 2>/dev/null || true
cp -r "$SCRIPT_DIR"/.git "$PROJECT_DIR/" 2>/dev/null || true

# Установка системных зависимостей для PostgreSQL (нужны для psycopg2-binary)
echo -e "${YELLOW}Установка системных зависимостей...${NC}"
apt-get install -y \
    python3 \
    python3.12-venv \
    python3-venv \
    python3-pip \
    git \
    curl \
    libpq-dev \
    postgresql-client \
    build-essential \
    python3.12-dev \
    python3-dev \
    pkg-config

# Обновляем PYTHON_VERSION после установки
if command -v python3 &> /dev/null; then
    PYTHON_VERSION="python3"
fi

# Установка Python и зависимостей
echo -e "${YELLOW}Проверка Python...${NC}"
if ! command -v $PYTHON_VERSION &> /dev/null; then
    echo -e "${RED}Ошибка: Python 3 не установлен${NC}"
    exit 1
fi

# Проверяем версию Python
PYTHON_VER=$($PYTHON_VERSION --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo -e "${GREEN}Найдена версия Python: $($PYTHON_VERSION --version)${NC}"

# Проверяем минимальную версию (3.10+, рекомендуется 3.12+)
PYTHON_MAJOR=$(echo $PYTHON_VER | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VER | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo -e "${RED}Ошибка: Требуется Python 3.10 или выше (рекомендуется 3.12+), найдена версия $PYTHON_VER${NC}"
    exit 1
fi
if [ "$PYTHON_MINOR" -lt 12 ]; then
    echo -e "${YELLOW}Предупреждение: Рекомендуется Python 3.12+, найдена версия $PYTHON_VER${NC}"
fi

# Создание виртуального окружения
echo -e "${YELLOW}Создание виртуального окружения...${NC}"
if [ ! -d "$PROJECT_DIR/venv" ]; then
    sudo -u "$SERVICE_USER" $PYTHON_VERSION -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}Виртуальное окружение создано${NC}"
else
    echo -e "${GREEN}Виртуальное окружение уже существует${NC}"
fi

# Установка зависимостей в виртуальное окружение
echo -e "${YELLOW}Установка зависимостей в виртуальное окружение...${NC}"
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install --upgrade pip setuptools wheel
sudo -u "$SERVICE_USER" "$PROJECT_DIR/venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

# Проверка наличия .env файла
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Создание шаблона .env файла...${NC}"
    cat > "$PROJECT_DIR/.env.example" << EOF
# Telegram Bot Settings
BOT_TOKEN='your_bot_token_here'
ADMIN_IDS='your_admin_id_here'

# PostgreSQL Database Settings (optional)
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DB_HOST=
DB_PORT=5432

# Timezone
TIMEZONE="Europe/Moscow"

# Telegram Channel ID for notifications
GROUP_ID=your_channel_id_here

# Price file ID (optional)
PRICE_FILE_ID=
EOF
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env.example"
    echo -e "${RED}ВНИМАНИЕ: Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создан шаблон .env.example. Скопируйте его в .env и заполните данные:${NC}"
    echo -e "${YELLOW}  cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env${NC}"
    echo -e "${YELLOW}  nano $PROJECT_DIR/.env${NC}"
else
    echo -e "${GREEN}Файл .env найден${NC}"
    chown "$SERVICE_USER:$SERVICE_USER" "$PROJECT_DIR/.env"
    chmod 600 "$PROJECT_DIR/.env"
fi

# Установка systemd service
echo -e "${YELLOW}Установка systemd service...${NC}"
cat > "/etc/systemd/system/$PROJECT_NAME.service" << EOF
[Unit]
Description=Telegram Bot "Объединяем компетенции"
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/main.py
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

# Перезагрузка systemd и включение сервиса
systemctl daemon-reload
systemctl enable "$PROJECT_NAME.service"

echo -e "${GREEN}=== Развертывание завершено! ===${NC}"
echo -e "${YELLOW}Следующие шаги:${NC}"
echo -e "1. Убедитесь, что файл .env настроен правильно:"
echo -e "   ${GREEN}nano $PROJECT_DIR/.env${NC}"
echo -e ""
echo -e "2. Запустите бота:"
echo -e "   ${GREEN}systemctl start $PROJECT_NAME${NC}"
echo -e ""
echo -e "3. Проверьте статус:"
echo -e "   ${GREEN}systemctl status $PROJECT_NAME${NC}"
echo -e ""
echo -e "4. Просмотр логов:"
echo -e "   ${GREEN}journalctl -u $PROJECT_NAME -f${NC}"
echo -e "   или"
echo -e "   ${GREEN}tail -f $PROJECT_DIR/logs/file.log${NC}"
