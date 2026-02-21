#!/bin/bash

# Скрипт для установки зависимостей в системный Python
# Использование: sudo ./install_dependencies.sh

set -e

PROJECT_DIR="/opt/clinic-bot"

echo "=== Установка зависимостей в системный Python ==="

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo "Ошибка: Запустите скрипт с правами root (sudo ./install_dependencies.sh)"
    exit 1
fi

# Определение версии Python
if command -v python3.12 &> /dev/null; then
    PYTHON="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON="python3.11"
elif command -v python3.10 &> /dev/null; then
    PYTHON="python3.10"
else
    PYTHON="python3"
fi

echo "Используется Python: $($PYTHON --version)"

# Установка системных зависимостей для PostgreSQL
echo "Установка системных зависимостей..."
apt-get update
apt-get install -y libpq-dev postgresql-client build-essential python3-dev pkg-config || true

# Обновление pip
echo "Обновление pip..."
$PYTHON -m pip install --upgrade pip setuptools wheel --break-system-packages

# Установка зависимостей
echo "Установка зависимостей из requirements.txt..."
$PYTHON -m pip install -r "$PROJECT_DIR/requirements.txt" --break-system-packages

# Проверка установки основных модулей
echo "Проверка установки модулей..."
$PYTHON -c "import structlog; import aiogram; print('✅ Основные модули установлены')"

echo "=== Зависимости установлены в системный Python! ==="
