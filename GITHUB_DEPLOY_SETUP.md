# 🚀 Настройка автоматического деплоя через GitHub Actions

## 📋 Пошаговая инструкция

### 1. Настройка GitHub Secrets

Перейдите в настройки GitHub репозитория: **Settings → Secrets and variables → Actions**

Добавьте следующие секреты:

#### `DROPLET_HOST`
```
104.248.39.106
```

#### `DROPLET_USER` 
```
coder
```

#### `DROPLET_SSH_KEY`
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACC6qgRzUzhSvYcp0wNHSmioMvrJng5h/gKFDD9OJBD1bQAAALDSMnPD0jJz
wwAAAAtzc2gtZWQyNTUxOQAAACC6qgRzUzhSvYcp0wNHSmioMvrJng5h/gKFDD9OJBD1bQ
AAAEDkheNEXt4GN3UJtZPH+pSoaUwxHzGHGrFTBhsTHCHafbqqBHNTOFK9hynTA0dKaKgy
+smeDmH+AoUMP04kEPVtAAAAJ2dpdGh1Yi1hY3Rpb25zLXZpcmFsaW5zdGFib3RAZGVwbG
95bWVudAECAwQFBg==
-----END OPENSSH PRIVATE KEY-----
```

### 2. Как работает автодеплой

✅ **Автоматический запуск:** При каждом push в ветку `main`
✅ **Тестирование:** Запуск тестов и линтинга
✅ **Docker деплой:** Пересборка и перезапуск контейнеров
✅ **Health check:** Проверка работоспособности после деплоя
✅ **Rollback:** Автоматический откат при ошибках

### 3. Workflow процесс

1. **Push в main** → GitHub Actions запускается
2. **Тестирование** → Проверка кода (pytest, flake8)
3. **SSH подключение** → Подключение к Droplet
4. **Git pull** → Загрузка изменений
5. **Docker rebuild** → Пересборка образа
6. **Container restart** → Перезапуск всех сервисов
7. **Health check** → Проверка работы бота
8. **Cleanup** → Очистка старых бэкапов

### 4. Мониторинг деплоя

- **GitHub Actions**: Просмотр логов деплоя в реальном времени
- **Droplet logs**: `docker-compose -f docker-compose.prod.yml logs -f bot`
- **Container status**: `docker-compose -f docker-compose.prod.yml ps`

### 5. Ручной деплой

Если нужно запустить деплой вручную:
1. Перейдите в **Actions** в GitHub репозитории
2. Выберите **Deploy to DigitalOcean Droplet**
3. Нажмите **Run workflow**

### 6. Состав деплоя

После деплоя будут обновлены:
- ✅ **Bot container** - основной Telegram бот
- ✅ **MCP Server** - Apify MCP сервер
- ✅ **Monitoring** - Prometheus, Grafana, Loki
- ✅ **Nginx** - Reverse proxy
- ✅ **Watchtower** - Автообновления Docker образов

### 7. Безопасность

- 🔒 SSH ключи зашифрованы в GitHub Secrets
- 🔒 Приватный ключ доступен только GitHub Actions
- 🔒 Публичный ключ добавлен в authorized_keys

## 🎯 Готово к использованию!

Теперь каждый push в `main` ветку автоматически обновит бота на продакшен сервере.

**Команда для тестирования:**
```bash
git add .
git commit -m "test: проверка автодеплоя"
git push origin main
```

Следите за прогрессом в разделе **Actions** на GitHub!