# Руководство по развертыванию Viralinstabot на DigitalOcean

## ✅ Что уже готово

1. **Dockerfile** - готов для контейнеризации
2. **docker-compose.yml** - для локальной разработки
3. **.dockerignore** - оптимизирует Docker образы
4. **GitHub Actions workflow** - автоматический CI/CD
5. **DigitalOcean App** - создано с ID: `86f9f85d-e92d-40c1-a756-3b00435e0dd6`

## 🔧 Что нужно сделать вручную

### 1. Создать GitHub репозиторий
```bash
# Создайте репозиторий на GitHub с именем 'viralinstabot'
# Затем добавьте remote:
git remote add origin https://github.com/Timosan61/viralinstabot.git
git push -u origin main
```

### 2. Настроить GitHub Secrets
Добавьте в Settings → Secrets and variables → Actions:
- `DIGITALOCEAN_ACCESS_TOKEN` - ваш DigitalOcean API токен
- `DO_APP_ID` - ID приложения: `86f9f85d-e92d-40c1-a756-3b00435e0dd6`

### 3. Обновить App Platform для GitHub интеграции
После создания репозитория обновите приложение:
```bash
# Через doctl или DigitalOcean панель
doctl apps update 86f9f85d-e92d-40c1-a756-3b00435e0dd6 --spec .do/app.yaml
```

### 4. Настроить переменные окружения в DigitalOcean
В App Platform Console добавьте:
- `TELEGRAM_BOT_TOKEN` (encrypted)
- `APIFY_API_TOKEN` (encrypted) 
- `OPENAI_API_KEY` (encrypted)

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