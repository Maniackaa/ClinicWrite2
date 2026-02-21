#!/bin/bash

# Простой скрипт для установки зависимостей
# Использование: sudo ./install_deps_simple.sh

set -e

PROJECT_DIR="/opt/clinic-bot"

echo "=== Установка зависимостей ==="

# Установка системных зависимостей
apt-get update
apt-get install -y libpq-dev postgresql-client build-essential python3-dev pkg-config || true

# Установка зависимостей из requirements.txt (игнорируем ошибки обновления системных пакетов)
echo "Установка зависимостей из requirements.txt..."
python3 -m pip install -r "$PROJECT_DIR/requirements.txt" --break-system-packages --no-warn-script-location

# Проверка установки
echo "Проверка установки..."
python3 -c "import structlog; import aiogram; print('✅ Основные модули установлены')" || {
    echo "Ошибка: модули не установлены"
    exit 1
}

echo "=== Готово! ==="
