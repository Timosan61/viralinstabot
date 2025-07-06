# Руководство по развертыванию Viralinstabot на DigitalOcean

## ✅ Что уже готово

1. **GitHub репозиторий** - https://github.com/Timosan61/viralinstabot
2. **Dockerfile** - готов для контейнеризации
3. **docker-compose.yml** - для локальной разработки
4. **.dockerignore** - оптимизирует Docker образы
5. **GitHub Actions workflow** - автоматический CI/CD
6. **DigitalOcean App** - создано с ID: `86f9f85d-e92d-40c1-a756-3b00435e0dd6`
7. **Код загружен** - все файлы в GitHub без секретных данных

## 🔧 Что нужно сделать вручную

### 1. Подключить GitHub к DigitalOcean App Platform
1. Откройте https://cloud.digitalocean.com/apps/86f9f85d-e92d-40c1-a756-3b00435e0dd6
2. Перейдите в **Settings** → **App-Level Settings**
3. Нажмите **Edit** рядом с Source
4. Выберите **GitHub** и авторизуйтесь
5. Выберите репозиторий: `Timosan61/viralinstabot`
6. Ветка: `main`
7. Включите **Auto Deploy**: `Yes`

### 2. Проверить переменные окружения
В App Platform Console проверьте, что установлены:
- `TELEGRAM_BOT_TOKEN` ✅ (уже установлен)
- `APIFY_API_TOKEN` ✅ (уже установлен)
- `OPENAI_API_KEY` ✅ (уже установлен)
- `ENV` = `production` ✅
- `DEBUG` = `False` ✅
- `DAILY_LIMIT` = `10` ✅
- `MONTHLY_LIMIT` = `10` ✅

### 3. Настроить GitHub Secrets (для CI/CD)
Добавьте в Settings → Secrets and variables → Actions:
- `DIGITALOCEAN_ACCESS_TOKEN` - ваш DigitalOcean API токен
- `DO_APP_ID` - ID приложения: `86f9f85d-e92d-40c1-a756-3b00435e0dd6`

## 🚀 Автоматическое обновление

После настройки GitHub интеграции:
- Каждый push в `main` ветку запускает деплой
- GitHub Actions проверяет код и тесты
- DigitalOcean автоматически деплоит изменения

## 🔍 Мониторинг

- **Логи**: DigitalOcean App Platform Console
- **Метрики**: CPU, Memory, Network в консоли DO
- **Алерты**: Настройте в Apps → Settings → Alerts

## 📁 Структура деплоя

```
/app/
├── src/           # Исходный код
├── data/          # Постоянные данные (база, отчеты)
├── logs/          # Логи приложения  
└── templates/     # Шаблоны отчетов
```

## 🛠 Команды управления

```bash
# Локальная разработка
docker-compose up -d

# Просмотр логов
doctl apps logs 86f9f85d-e92d-40c1-a756-3b00435e0dd6

# Перезапуск приложения
doctl apps create-deployment 86f9f85d-e92d-40c1-a756-3b00435e0dd6

# Масштабирование
doctl apps update 86f9f85d-e92d-40c1-a756-3b00435e0dd6 --spec .do/app.yaml
```

## 💰 Стоимость

- **App Platform Professional**: ~$12/месяц (1vCPU, 1GB RAM)
- **Дополнительные costs**: bandwidth, database (если используется)

## 🔒 Безопасность

- Все секретные переменные зашифрованы
- HTTPS по умолчанию
- Изоляция контейнеров
- Автоматические обновления безопасности

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в DigitalOcean Console
2. Проверьте статус GitHub Actions
3. Убедитесь, что все переменные окружения настроены