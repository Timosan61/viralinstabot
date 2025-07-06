# 🚀 Шаблоны для автодеплоя

Эта папка содержит готовые шаблоны для настройки автоматического деплоя GitHub Actions → Сервер в ваших проектах.

## 📁 Содержание

### 🔧 Основные файлы

| Файл | Описание | Использование |
|------|----------|---------------|
| `github-workflow-template.yml` | GitHub Actions workflow | Скопируйте в `.github/workflows/deploy.yml` |
| `docker-compose-template.yml` | Docker Compose конфигурация | Скопируйте в `docker-compose.prod.yml` |
| `dockerfile-template` | Dockerfile шаблоны | Скопируйте в `Dockerfile` |
| `secrets-checklist.md` | Checklist для настройки секретов | Руководство по настройке |

### 📖 Документация

- **[Главное руководство](../AUTODEPLOY_GUIDE.md)** - полная инструкция по настройке
- **[Checklist секретов](secrets-checklist.md)** - пошаговая настройка GitHub Secrets

## 🎯 Быстрый старт

### 1. Копирование файлов

```bash
# В корне вашего проекта создайте:
mkdir -p .github/workflows

# Скопируйте и адаптируйте шаблоны:
cp templates/deployment/github-workflow-template.yml .github/workflows/deploy.yml
cp templates/deployment/docker-compose-template.yml docker-compose.prod.yml
cp templates/deployment/dockerfile-template Dockerfile
```

### 2. Настройка SSH ключей

```bash
# На вашем сервере:
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -N "" -C "github-deploy@$(hostname)"
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys ~/.ssh/github_deploy
```

### 3. GitHub Secrets

Добавьте в GitHub репозиторий (**Settings → Secrets and variables → Actions**):

- `SERVER_HOST` - IP адрес сервера
- `SERVER_USER` - имя пользователя  
- `SERVER_SSH_KEY` - приватный SSH ключ (ПОЛНОСТЬЮ)

### 4. Адаптация шаблонов

Отредактируйте файлы, заменив:
- `YOUR_PROJECT_NAME` → название вашего проекта
- `YOUR_APP_DIR` → путь к приложению на сервере
- `YOUR_PORT` → порт вашего приложения
- Команды тестов и сборки под ваш стек технологий

## 🔧 Поддерживаемые технологии

### Языки программирования
- ✅ **Python** (готовые примеры)
- ✅ **Node.js** (готовые примеры)
- ✅ **Go** (готовые примеры)
- 🔄 **PHP, Java, .NET** (легко адаптируется)

### Типы деплоя
- ✅ **Docker & Docker Compose** (рекомендуется)
- ✅ **Systemd сервисы**
- ✅ **Процесс в фоне**

### Облачные провайдеры
- ✅ **DigitalOcean Droplets**
- ✅ **AWS EC2**
- ✅ **Google Cloud Compute Engine**
- ✅ **Azure Virtual Machines**
- ✅ **Любые VPS с SSH доступом**

## 📊 Включенные возможности

### CI/CD Pipeline
- ✅ Автоматическое тестирование (pytest, npm test, go test)
- ✅ Линтинг кода (flake8, eslint, golint)
- ✅ Кэширование зависимостей
- ✅ Параллельные джобы

### Деплой
- ✅ SSH подключение с ключами
- ✅ Docker сборка и перезапуск
- ✅ Health checks
- ✅ Автоматический откат при ошибках
- ✅ Бэкапы перед деплоем

### Мониторинг
- ✅ Prometheus метрики
- ✅ Grafana дашборды
- ✅ Loki логирование
- ✅ Уведомления (Slack, Email)

### Безопасность
- ✅ Зашифрованные SSH ключи
- ✅ Пользователи без root прав
- ✅ Изоляция контейнеров
- ✅ Минимальные права доступа

## 🛠 Кастомизация

### Для Python проекта

```yaml
# В github-workflow-template.yml раскомментируйте:
- name: Set up Python 3.11
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Run Python tests
  run: python -m pytest tests/ -v
```

### Для Node.js проекта

```yaml
# В github-workflow-template.yml раскомментируйте:
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18'

- name: Run Node.js tests
  run: npm test
```

### Для Go проекта

```yaml
# В github-workflow-template.yml раскомментируйте:
- name: Set up Go
  uses: actions/setup-go@v4
  with:
    go-version: '1.21'

- name: Run Go tests
  run: go test ./...
```

## 📋 Checklist адаптации

### ✅ Подготовка
- [ ] Скопировать шаблоны в проект
- [ ] Создать SSH ключи на сервере
- [ ] Настроить GitHub Secrets
- [ ] Адаптировать названия проекта

### ✅ Конфигурация
- [ ] Выбрать язык программирования в workflow
- [ ] Настроить команды тестов
- [ ] Адаптировать Dockerfile под ваш стек
- [ ] Настроить порты и volumes в docker-compose

### ✅ Тестирование
- [ ] Протестировать SSH подключение
- [ ] Запустить тестовый деплой
- [ ] Проверить health checks
- [ ] Убедиться в работе отката

### ✅ Продакшен
- [ ] Настроить мониторинг
- [ ] Добавить уведомления
- [ ] Создать процедуры бэкапа
- [ ] Документировать процесс

## 🚨 Устранение проблем

### Частые ошибки

1. **SSH connection failed**
   - Проверьте права на SSH ключи: `chmod 600 ~/.ssh/github_deploy`
   - Убедитесь, что ключ полностью скопирован в GitHub Secrets

2. **Docker build failed**
   - Проверьте синтаксис Dockerfile
   - Убедитесь, что все необходимые файлы присутствуют

3. **Health check failed**
   - Адаптируйте health check под ваше приложение
   - Увеличьте время ожидания start_period

4. **Permission denied**
   - Проверьте права пользователя на директорию приложения
   - Убедитесь, что пользователь в группе docker

### Отладка

```bash
# На сервере проверьте:
docker-compose -f docker-compose.prod.yml logs
systemctl status docker
df -h  # свободное место
free -m  # память
```

## 🔗 Полезные ссылки

- **[Главное руководство](../AUTODEPLOY_GUIDE.md)** - детальная документация
- **[GitHub Actions документация](https://docs.github.com/en/actions)**
- **[Docker Compose документация](https://docs.docker.com/compose/)**
- **[SSH ключи лучшие практики](https://wiki.archlinux.org/title/SSH_keys)**

## 💡 Советы

1. **Тестируйте на staging** перед применением в production
2. **Используйте Docker** для консистентности окружений
3. **Настройте мониторинг** с самого начала
4. **Ротируйте SSH ключи** каждые 6-12 месяцев
5. **Создавайте бэкапы** перед каждым деплоем

---

🎉 **Успешного деплоя!** Если возникли вопросы, изучите [главное руководство](../AUTODEPLOY_GUIDE.md) или создайте issue в репозитории.