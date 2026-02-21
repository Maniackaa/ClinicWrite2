# Инструкция по развертыванию бота на сервере

## Требования

- Ubuntu/Debian сервер
- Python 3.10 или выше
- Права root (sudo)

## Быстрая установка

### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и необходимых пакетов
sudo apt install -y python3.10 python3.10-venv python3-pip git
```

### 2. Клонирование репозитория

```bash
# Клонирование проекта
cd /opt
sudo git clone https://github.com/Maniackaa/ClinicWrite.git clinic-bot
cd clinic-bot
```

### 3. Развертывание

```bash
# Сделать скрипт исполняемым
sudo chmod +x deploy.sh

# Запустить развертывание
sudo ./deploy.sh
```

Скрипт автоматически:
- Создаст пользователя `clinicbot`
- Установит зависимости в виртуальное окружение
- Настроит systemd service
- Создаст шаблон .env файла (если его нет)

### 4. Настройка .env файла

```bash
# Если файл .env не существует, скопируйте шаблон
sudo cp /opt/clinic-bot/.env.example /opt/clinic-bot/.env

# Отредактируйте файл
sudo nano /opt/clinic-bot/.env
```

Заполните обязательные поля:
- `BOT_TOKEN` - токен бота от @BotFather
- `ADMIN_IDS` - ваш Telegram ID
- `GROUP_ID` - ID канала для уведомлений о заявках

### 5. Запуск бота

```bash
# Запуск бота
sudo systemctl start clinic-bot

# Включение автозапуска при перезагрузке
sudo systemctl enable clinic-bot

# Проверка статуса
sudo systemctl status clinic-bot
```

## Управление ботом

### Просмотр логов

```bash
# Логи systemd
sudo journalctl -u clinic-bot -f

# Или логи из файла
tail -f /opt/clinic-bot/logs/file.log
```

### Управление сервисом

```bash
# Запуск
sudo systemctl start clinic-bot

# Остановка
sudo systemctl stop clinic-bot

# Перезапуск
sudo systemctl restart clinic-bot

# Статус
sudo systemctl status clinic-bot

# Отключение автозапуска
sudo systemctl disable clinic-bot
```

## Обновление бота

```bash
cd /opt/clinic-bot

# Остановить бота
sudo systemctl stop clinic-bot

# Обновить код
sudo git pull

# Обновить зависимости (если изменились)
sudo -u clinicbot /opt/clinic-bot/venv/bin/pip install -r requirements.txt

# Запустить бота
sudo systemctl start clinic-bot
```

## Альтернативный способ установки (только systemd service)

Если проект уже развернут, можно установить только systemd service:

```bash
sudo chmod +x install.sh
sudo ./install.sh
```

## Структура проекта на сервере

```
/opt/clinic-bot/
├── main.py                 # Главный файл бота
├── handlers/              # Обработчики
├── keyboards/             # Клавиатуры
├── config_data/           # Конфигурация
├── data/                  # Данные (фото врачей, прайс)
├── logs/                  # Логи
├── venv/                  # Виртуальное окружение
└── .env                   # Переменные окружения
```

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
   ```bash
   sudo journalctl -u clinic-bot -n 50
   ```

2. Проверьте файл .env:
   ```bash
   sudo cat /opt/clinic-bot/.env
   ```

3. Проверьте права доступа:
   ```bash
   sudo ls -la /opt/clinic-bot/
   ```

### Ошибка прав доступа

```bash
sudo chown -R clinicbot:clinicbot /opt/clinic-bot
```

### Ошибка импорта модулей

```bash
# Переустановка зависимостей
sudo -u clinicbot /opt/clinic-bot/venv/bin/pip install -r /opt/clinic-bot/requirements.txt
```

## Безопасность

- Файл `.env` должен иметь права доступа 600:
  ```bash
  sudo chmod 600 /opt/clinic-bot/.env
  ```

- Не коммитьте `.env` файл в git (он уже в .gitignore)

- Регулярно обновляйте зависимости для безопасности
