# 🚀 Развертывание Viralinstabot на DigitalOcean Droplet

## 📋 Обзор

Это руководство покажет, как бесплатно развернуть Telegram-бота на вашем существующем DigitalOcean Droplet с полным автоматическим CI/CD пайплайном.

## 🎯 Преимущества Droplet vs App Platform

| Критерий | Droplet | App Platform |
|----------|---------|--------------|
| **Стоимость** | ✅ Бесплатно (на существующем) | 💰 $12+/месяц |
| **Контроль** | ✅ Полный | ⚠️ Ограниченный |
| **Производительность** | ✅ Выделенные ресурсы | ⚠️ Shared |
| **Мониторинг** | ✅ Детальный | ⚠️ Базовый |
| **Кастомизация** | ✅ Неограниченная | ❌ Ограниченная |

## 📋 Требования

- **DigitalOcean Droplet** с Ubuntu 20.04+ 
- **Минимум 1GB RAM** (рекомендуется 2GB)
- **SSH доступ** к серверу
- **Домен** (опционально)

## 🛠 Способы развертывания

### Способ 1: Автоматическая установка (Рекомендуется)

```bash
# На вашем Droplet выполните:
curl -fsSL https://raw.githubusercontent.com/Timosan61/viralinstabot/main/deploy/install_droplet.sh | sudo bash
```

### Способ 2: Ручная установка

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-venv git curl wget unzip supervisor nginx ufw htop fail2ban
```

#### 2. Создание пользователя

```bash
# Создание пользователя для бота
sudo useradd -r -s /bin/bash -m -d /home/botuser botuser
```

#### 3. Клонирование репозитория

```bash
# Создание директории приложения
sudo mkdir -p /opt/viralinstabot
cd /opt/viralinstabot

# Клонирование кода
sudo git clone https://github.com/Timosan61/viralinstabot.git .
sudo chown -R botuser:botuser /opt/viralinstabot
```

#### 4. Настройка Python окружения

```bash
# Создание виртуального окружения
sudo -u botuser python3 -m venv venv
sudo -u botuser bash -c "source venv/bin/activate && pip install -r requirements.txt"
```

#### 5. Конфигурация

```bash
# Создание .env файла
sudo -u botuser cp .env.example .env

# Редактирование конфигурации
sudo nano /opt/viralinstabot/.env
```

Добавьте ваши API токены:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
APIFY_API_TOKEN=your_apify_token  
OPENAI_API_KEY=your_openai_key
ENV=production
DEBUG=False
```

### Способ 3: Docker Compose (Продвинутый)

```bash
# Клонирование и запуск
cd /opt/viralinstabot
sudo docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Управление сервисом

### Systemd команды

```bash
# Запуск
sudo systemctl start viralinstabot.service

# Остановка
sudo systemctl stop viralinstabot.service

# Перезапуск
sudo systemctl restart viralinstabot.service

# Статус
sudo systemctl status viralinstabot.service

# Логи
sudo journalctl -u viralinstabot.service -f
```

### Удобные команды

```bash
# Управление ботом
botctl start|stop|restart|status|logs|update

# Обновление бота
/opt/viralinstabot/update_bot.sh
```

## 🔄 Автоматическое обновление через GitHub Actions

### 1. Настройка SSH ключей

На вашем Droplet:
```bash
# Создание SSH ключа для GitHub Actions
ssh-keygen -t ed25519 -f ~/.ssh/github_actions -N ""

# Добавление публичного ключа в authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Вывод приватного ключа (скопируйте для GitHub Secrets)
cat ~/.ssh/github_actions
```

### 2. Настройка GitHub Secrets

В настройках GitHub репозитория добавьте:

- `DROPLET_HOST` - IP адрес вашего Droplet
- `DROPLET_USER` - имя пользователя (обычно `root`)
- `DROPLET_SSH_KEY` - приватный SSH ключ

### 3. Автоматический деплой

Теперь каждый push в `main` ветку автоматически обновит бота на Droplet!

## 📊 Мониторинг и логирование

### Системные логи

```bash
# Логи бота
sudo journalctl -u viralinstabot.service -f

# Системные логи
sudo tail -f /var/log/syslog

# Логи приложения
tail -f /opt/viralinstabot/logs/bot.log
```

### Docker мониторинг (если используете)

```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи
docker-compose -f docker-compose.prod.yml logs -f bot

# Ресурсы
docker stats
```

### Веб-мониторинг

Если включили полный stack мониторинга:
- **Grafana**: http://your-server:3000 (admin/admin)
- **Prometheus**: http://your-server:9090

## 🔒 Безопасность

### Firewall

```bash
# Базовая настройка UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw status
```

### Fail2Ban

```bash
# Проверка статуса
sudo fail2ban-client status

# Логи
sudo tail -f /var/log/fail2ban.log
```

### SSL (если нужен веб-интерфейс)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com
```

## 📈 Производительность

### Оптимизация ресурсов

```bash
# Мониторинг ресурсов
htop
df -h
free -m

# Очистка логов
sudo journalctl --vacuum-time=7d
```

### Настройка swap (для маленьких Droplet)

```bash
# Создание swap файла 1GB
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Автомонтирование
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## 🆘 Устранение неполадок

### Общие проблемы

1. **Бот не запускается**
   ```bash
   # Проверка логов
   sudo journalctl -u viralinstabot.service -n 50
   
   # Проверка конфигурации
   sudo -u botuser bash -c "cd /opt/viralinstabot && source venv/bin/activate && python -m src.bot.main"
   ```

2. **Проблемы с зависимостями**
   ```bash
   # Переустановка зависимостей
   sudo -u botuser bash -c "cd /opt/viralinstabot && source venv/bin/activate && pip install -r requirements.txt --force-reinstall"
   ```

3. **Нехватка места**
   ```bash
   # Очистка
   sudo apt autoremove
   sudo docker system prune -a
   sudo journalctl --vacuum-size=100M
   ```

### Восстановление из бэкапа

```bash
# Список бэкапов
ls -la /opt/viralinstabot.backup.*

# Восстановление
sudo systemctl stop viralinstabot.service
sudo mv /opt/viralinstabot /opt/viralinstabot.broken
sudo mv /opt/viralinstabot.backup.YYYYMMDD_HHMMSS /opt/viralinstabot
sudo systemctl start viralinstabot.service
```

## 💰 Стоимость

| Компонент | Droplet | App Platform |
|-----------|---------|--------------|
| **Основное приложение** | $0 (на существующем) | $12/месяц |
| **Мониторинг** | $0 | $5+/месяц |
| **Базы данных** | $0 | $15+/месяц |
| **SSL сертификаты** | $0 (Let's Encrypt) | Включено |
| **Backup** | $0 (ручной) | Включено |

**Итого**: $0 vs $32+/месяц

## 📞 Поддержка

- **Логи**: `sudo journalctl -u viralinstabot.service -f`
- **Статус**: `botctl status`
- **Обновление**: `botctl update`
- **GitHub Issues**: https://github.com/Timosan61/viralinstabot/issues

## 🎉 Готово!

После установки ваш бот будет:
- ✅ Автоматически запускаться при загрузке сервера
- ✅ Автоматически обновляться при push в GitHub
- ✅ Логировать все события
- ✅ Восстанавливаться после сбоев
- ✅ Работать стабильно 24/7

**Команда для быстрого запуска:**
```bash
curl -fsSL https://raw.githubusercontent.com/Timosan61/viralinstabot/main/deploy/install_droplet.sh | sudo bash
```