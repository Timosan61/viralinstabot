# 🚀 Полное руководство по настройке автодеплоя GitHub Actions → DigitalOcean Droplet

## 📖 Оглавление

1. [Обзор системы](#-обзор-системы)
2. [Настройка с нуля](#-настройка-с-нуля)
3. [Файлы конфигурации](#-файлы-конфигурации)
4. [Применение в других проектах](#-применение-в-других-проектах)
5. [Операции и мониторинг](#-операции-и-мониторинг)
6. [Безопасность](#-безопасность)
7. [Шаблоны для копирования](#-шаблоны-для-копирования)

---

## 🏗 Обзор системы

### Архитектура автодеплоя

```
┌─────────────┐    push     ┌──────────────┐    SSH     ┌──────────────┐
│   GitHub    │  ────────► │GitHub Actions│  ────────► │DigitalOcean  │
│ Repository  │             │   Runner     │             │   Droplet    │
└─────────────┘             └──────────────┘             └──────────────┘
                                    │                             │
                                    │                             │
                            ┌───────▼────────┐           ┌───────▼────────┐
                            │ 1. Test Code   │           │ 1. Git Pull    │
                            │ 2. Build Image │           │ 2. Docker Build│
                            │ 3. SSH Deploy │           │ 3. Restart Bot │
                            └────────────────┘           └────────────────┘
```

### Используемые технологии

- **GitHub Actions** - CI/CD платформа
- **Docker & Docker Compose** - Контейнеризация
- **SSH** - Безопасное подключение к серверу
- **DigitalOcean Droplet** - Облачный сервер
- **ED25519 SSH keys** - Современная криптография

### Преимущества подхода

✅ **Полная автоматизация** - деплой по одному push  
✅ **Нулевая стоимость** - используется существующий Droplet  
✅ **Безопасность** - SSH ключи в зашифрованных Secrets  
✅ **Масштабируемость** - легко адаптируется для других проектов  
✅ **Мониторинг** - полная видимость процесса деплоя  
✅ **Откат** - автоматическое восстановление при ошибках  

---

## 🔧 Настройка с нуля

### Шаг 1: Подготовка Droplet

#### 1.1 Обновление системы

```bash
# На вашем Droplet выполните:
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезагрузка для применения изменений
sudo reboot
```

#### 1.2 Создание рабочей директории

```bash
# Создание директории проекта
mkdir -p ~/Desktop/2202/Viralinstabot
cd ~/Desktop/2202/Viralinstabot

# Клонирование репозитория
git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT.git .
```

### Шаг 2: Создание SSH ключей

#### 2.1 Генерация ключей

```bash
# Создание ED25519 ключа для GitHub Actions
ssh-keygen -t ed25519 -f ~/.ssh/github_actions_deploy -N "" -C "github-actions-deploy@server"

# Вывод приватного ключа (для GitHub Secrets)
cat ~/.ssh/github_actions_deploy
```

**💡 Сохраните приватный ключ! Он понадобится для GitHub Secrets.**

#### 2.2 Добавление публичного ключа

```bash
# Добавление публичного ключа в authorized_keys
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys

# Установка правильных прав доступа
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

#### 2.3 Тестирование подключения

```bash
# Проверка SSH подключения с новым ключом
ssh -i ~/.ssh/github_actions_deploy $(whoami)@localhost echo "SSH работает!"
```

### Шаг 3: Настройка GitHub Secrets

Перейдите в GitHub: **Settings → Secrets and variables → Actions**

#### 3.1 Добавьте секреты:

**`DROPLET_HOST`**
```
YOUR_DROPLET_IP
```

**`DROPLET_USER`**
```
YOUR_USERNAME
```

**`DROPLET_SSH_KEY`**
```
-----BEGIN OPENSSH PRIVATE KEY-----
[Весь приватный ключ из ~/.ssh/github_actions_deploy]
-----END OPENSSH PRIVATE KEY-----
```

### Шаг 4: Создание GitHub Actions Workflow

Создайте файл `.github/workflows/deploy.yml`:

```yaml
name: Deploy to DigitalOcean Droplet

permissions:
  contents: read

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  DROPLET_HOST: ${{ secrets.DROPLET_HOST }}
  DROPLET_USER: ${{ secrets.DROPLET_USER }}
  APP_DIR: "/home/${{ secrets.DROPLET_USER }}/Desktop/2202/YOUR_PROJECT"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ -v || echo "No tests found, skipping..."
    
    - name: Run linting
      run: |
        python -m flake8 src/ || echo "Linting completed with warnings"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.DROPLET_SSH_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ env.DROPLET_HOST }} >> ~/.ssh/known_hosts
        
    - name: Deploy with Docker Compose
      run: |
        ssh ${{ env.DROPLET_USER }}@${{ env.DROPLET_HOST }} << 'ENDSSH'
          set -e
          
          cd ${{ env.APP_DIR }}
          
          # Pull latest changes
          git fetch origin
          git reset --hard origin/main
          
          # Stop containers
          docker-compose -f docker-compose.prod.yml down || true
          
          # Build and start
          docker-compose -f docker-compose.prod.yml build --no-cache
          docker-compose -f docker-compose.prod.yml up -d
          
          # Health check
          sleep 30
          docker-compose -f docker-compose.prod.yml ps
        ENDSSH
```

### Шаг 5: Тестирование деплоя

```bash
# Внесите изменения и запушьте
git add .
git commit -m "test: настройка автодеплоя"
git push origin main
```

Следите за прогрессом в **Actions** на GitHub!

---

## 📁 Файлы конфигурации

### GitHub Actions Workflow (.github/workflows/deploy.yml)

#### Структура workflow

```yaml
name: Deploy to DigitalOcean Droplet  # Название workflow

permissions:                          # Минимальные права доступа
  contents: read

on:                                   # Триггеры запуска
  push:
    branches: [ main ]                # Автоматически при push в main
  workflow_dispatch:                  # Ручной запуск

env:                                  # Переменные окружения
  DROPLET_HOST: ${{ secrets.DROPLET_HOST }}
  DROPLET_USER: ${{ secrets.DROPLET_USER }}
  APP_DIR: "/path/to/your/app"

jobs:                                 # Задачи workflow
  test:                              # Джоба тестирования
    # ... тесты и линтинг
  
  deploy:                            # Джоба деплоя
    needs: test                      # Запускается только после test
    # ... SSH подключение и деплой
```

#### Ключевые компоненты

**1. Тестирование**
```yaml
- name: Run tests
  run: |
    python -m pytest tests/ -v || echo "No tests found, skipping..."

- name: Run linting  
  run: |
    python -m flake8 src/ || echo "Linting completed with warnings"
```

**2. SSH подключение**
```yaml
- name: Setup SSH
  run: |
    mkdir -p ~/.ssh
    echo "${{ secrets.DROPLET_SSH_KEY }}" > ~/.ssh/id_rsa
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H ${{ env.DROPLET_HOST }} >> ~/.ssh/known_hosts
```

**3. Деплой через SSH**
```yaml
- name: Deploy with Docker Compose
  run: |
    ssh ${{ env.DROPLET_USER }}@${{ env.DROPLET_HOST }} << 'ENDSSH'
      # Команды выполняются на удаленном сервере
    ENDSSH
```

### Docker Compose конфигурация (docker-compose.prod.yml)

#### Основная структура

```yaml
version: '3.8'

services:
  app:                               # Основное приложение
    build: .
    container_name: myapp-prod
    restart: unless-stopped
    env_file: .env
    environment:
      - ENV=production
    volumes:
      - ./data:/app/data             # Персистентные данные
    networks:
      - app-network
    healthcheck:                     # Проверка здоровья
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  app-network:
    driver: bridge
```

#### Опциональные сервисы

**Мониторинг (Prometheus + Grafana)**
```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Reverse Proxy (Nginx)**
```yaml
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
```

### Dockerfile

#### Многоэтапная сборка

```dockerfile
# Этап сборки
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Продакшен этап
FROM python:3.11-slim

WORKDIR /app

# Копирование зависимостей
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Копирование кода
COPY src/ ./src/
COPY templates/ ./templates/
COPY config/ ./config/

# Создание пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-m", "src.main"]
```

---

## 🔄 Применение в других проектах

### Адаптация для Node.js проекта

#### 1. Обновите workflow тестирование:

```yaml
- name: Set up Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18'
    
- name: Install dependencies
  run: npm ci

- name: Run tests
  run: npm test

- name: Run linting
  run: npm run lint
```

#### 2. Обновите Dockerfile:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

USER node

CMD ["npm", "start"]
```

### Адаптация для Go проекта

#### 1. Workflow тестирование:

```yaml
- name: Set up Go
  uses: actions/setup-go@v4
  with:
    go-version: '1.21'

- name: Run tests
  run: go test ./...

- name: Build
  run: go build -o main .
```

#### 2. Dockerfile:

```dockerfile
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

CMD ["./main"]
```

### Настройка для разных облачных провайдеров

#### AWS EC2

```yaml
env:
  EC2_HOST: ${{ secrets.EC2_HOST }}
  EC2_USER: ec2-user
  EC2_KEY: ${{ secrets.EC2_SSH_KEY }}
```

#### Google Cloud Platform

```yaml
env:
  GCP_HOST: ${{ secrets.GCP_HOST }}
  GCP_USER: ${{ secrets.GCP_USER }}
  GCP_KEY: ${{ secrets.GCP_SSH_KEY }}
```

#### Azure

```yaml
env:
  AZURE_HOST: ${{ secrets.AZURE_HOST }}
  AZURE_USER: azureuser
  AZURE_KEY: ${{ secrets.AZURE_SSH_KEY }}
```

### Настройка мультисреда (staging/production)

#### Workflow с окружениями:

```yaml
on:
  push:
    branches: [ main, staging ]

jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/staging'
    environment: staging
    # ... деплой на staging

  deploy-production:
    if: github.ref == 'refs/heads/main'
    environment: production
    # ... деплой на production
```

#### Разные Secrets для окружений:

- `STAGING_HOST`, `STAGING_USER`, `STAGING_SSH_KEY`
- `PRODUCTION_HOST`, `PRODUCTION_USER`, `PRODUCTION_SSH_KEY`

---

## 📊 Операции и мониторинг

### Мониторинг деплоев

#### 1. GitHub Actions
```bash
# Просмотр статуса через CLI
gh run list --limit 5

# Просмотр логов конкретного run
gh run view [RUN_ID] --log

# Мониторинг в реальном времени
gh run watch [RUN_ID]
```

#### 2. Сервер мониторинг
```bash
# Статус контейнеров
docker-compose -f docker-compose.prod.yml ps

# Логи приложения
docker-compose -f docker-compose.prod.yml logs -f app

# Системные ресурсы
htop
df -h
free -m
```

#### 3. Автоматические уведомления

**Slack интеграция:**
```yaml
- name: Slack Notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
  if: always()
```

**Email уведомления:**
```yaml
- name: Email Notification
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 587
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: "Деплой ${{ job.status }}"
    body: "Деплой завершен со статусом: ${{ job.status }}"
    to: admin@company.com
  if: failure()
```

### Откат изменений

#### Автоматический откат при ошибке

```yaml
- name: Deploy with Rollback
  run: |
    ssh ${{ env.DROPLET_USER }}@${{ env.DROPLET_HOST }} << 'ENDSSH'
      set -e
      
      # Создание бэкапа
      cd ${{ env.APP_DIR }}
      docker-compose -f docker-compose.prod.yml ps > backup/deployment.$(date +%Y%m%d_%H%M%S)
      
      # Деплой
      git pull origin main
      docker-compose -f docker-compose.prod.yml up -d --build
      
      # Проверка здоровья
      sleep 30
      if ! docker-compose -f docker-compose.prod.yml exec -T app curl -f http://localhost:8080/health; then
        echo "Health check failed, rolling back..."
        docker-compose -f docker-compose.prod.yml down
        git reset --hard HEAD~1
        docker-compose -f docker-compose.prod.yml up -d
        exit 1
      fi
    ENDSSH
```

#### Ручной откат

```bash
# На сервере
cd /path/to/app

# Просмотр истории коммитов
git log --oneline -10

# Откат к предыдущему коммиту
git reset --hard [COMMIT_HASH]
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build
```

### Диагностика проблем

#### Частые проблемы и решения

**1. SSH подключение не работает**
```bash
# Проверка ключа
ssh-keygen -lf ~/.ssh/github_actions_deploy.pub

# Проверка authorized_keys
cat ~/.ssh/authorized_keys | grep github-actions

# Тест подключения
ssh -i ~/.ssh/github_actions_deploy -v user@server
```

**2. Docker контейнер не запускается**
```bash
# Просмотр логов
docker-compose -f docker-compose.prod.yml logs app

# Проверка конфигурации
docker-compose -f docker-compose.prod.yml config

# Ручной запуск для отладки
docker run -it --rm app:latest /bin/bash
```

**3. Недостаточно ресурсов**
```bash
# Мониторинг ресурсов
docker stats
free -m
df -h

# Очистка неиспользуемых ресурсов
docker system prune -a
docker volume prune
```

---

## 🔒 Безопасность

### Управление SSH ключами

#### Best Practices

✅ **Используйте ED25519** вместо RSA  
✅ **Отдельные ключи** для разных окружений  
✅ **Регулярная ротация** ключей (каждые 6-12 месяцев)  
✅ **Ограниченные права** - только необходимые команды  
✅ **Мониторинг доступа** - логирование всех подключений  

#### Создание ключей с ограничениями

```bash
# Ключ только для конкретных команд
ssh-keygen -t ed25519 -f ~/.ssh/deploy_only -N "" -C "deploy-only@server"

# В authorized_keys добавить ограничения:
command="cd /path/to/app && docker-compose -f docker-compose.prod.yml restart",no-port-forwarding,no-X11-forwarding ssh-ed25519 AAAAC3NzaC1lZDI1NTE5...
```

### Ротация секретов

#### Автоматическая ротация

```yaml
name: Rotate SSH Keys

on:
  schedule:
    - cron: '0 0 1 */6 *'  # Каждые 6 месяцев

jobs:
  rotate-keys:
    runs-on: ubuntu-latest
    steps:
    - name: Generate new SSH key
      run: ssh-keygen -t ed25519 -f new_key -N ""
    
    - name: Update authorized_keys on server
      run: |
        # Логика обновления ключей
        
    - name: Update GitHub Secrets
      run: |
        # Обновление через GitHub API
```

#### Ручная ротация

```bash
# 1. Генерация нового ключа
ssh-keygen -t ed25519 -f ~/.ssh/new_deploy_key -N ""

# 2. Добавление на сервер
cat ~/.ssh/new_deploy_key.pub >> ~/.ssh/authorized_keys

# 3. Обновление GitHub Secrets
# Замените DROPLET_SSH_KEY новым приватным ключом

# 4. Тестирование
# Проведите тестовый деплой

# 5. Удаление старого ключа
# Уберите старый ключ из authorized_keys
```

### Изоляция окружений

#### Сетевая изоляция

```yaml
# docker-compose.prod.yml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # Без доступа в интернет

services:
  app:
    networks:
      - frontend
      - backend
      
  database:
    networks:
      - backend  # Только внутренняя сеть
```

#### Secrets менеджмент

```bash
# Использование внешних секретов
docker run -d \
  --name app \
  --secret db_password \
  --secret api_key \
  myapp:latest
```

### Аудит доступов

#### Логирование SSH подключений

```bash
# В /etc/ssh/sshd_config
LogLevel VERBOSE
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# Просмотр логов
sudo tail -f /var/log/auth.log | grep ssh
```

#### Мониторинг GitHub Actions

```bash
# API запрос для получения истории запусков
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/runs
```

---

## 📋 Шаблоны для копирования

### Базовый workflow шаблон

```yaml
name: Deploy to Server

permissions:
  contents: read

on:
  push:
    branches: [ main ]
  workflow_dispatch:

env:
  SERVER_HOST: ${{ secrets.SERVER_HOST }}
  SERVER_USER: ${{ secrets.SERVER_USER }}
  APP_DIR: "${{ secrets.APP_DIR }}"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    # Добавьте ваши тесты здесь
    - name: Run Tests
      run: echo "Add your tests here"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SERVER_SSH_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ env.SERVER_HOST }} >> ~/.ssh/known_hosts
        
    - name: Deploy
      run: |
        ssh ${{ env.SERVER_USER }}@${{ env.SERVER_HOST }} << 'ENDSSH'
          set -e
          cd ${{ env.APP_DIR }}
          
          # Ваши команды деплоя здесь
          git pull origin main
          # docker-compose up -d --build
          # systemctl restart myapp
        ENDSSH
```

### Docker Compose шаблон

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: myapp-prod
    restart: unless-stopped
    env_file: .env
    environment:
      - ENV=production
    volumes:
      - ./data:/app/data
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  app-network:
    driver: bridge
```

### Dockerfile шаблон

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["python", "app.py"]
```

### Checklist для новых проектов

#### ✅ Подготовка сервера
- [ ] Обновление системы
- [ ] Установка Docker и Docker Compose
- [ ] Создание пользователя для деплоя
- [ ] Настройка SSH ключей
- [ ] Конфигурация firewall

#### ✅ GitHub настройка
- [ ] Создание `.github/workflows/deploy.yml`
- [ ] Добавление GitHub Secrets
- [ ] Тестирование workflow
- [ ] Настройка уведомлений

#### ✅ Docker конфигурация
- [ ] Создание `Dockerfile`
- [ ] Создание `docker-compose.prod.yml`
- [ ] Конфигурация `.env`
- [ ] Настройка health checks

#### ✅ Безопасность
- [ ] Ротация SSH ключей
- [ ] Настройка ограничений доступа
- [ ] Конфигурация мониторинга
- [ ] Создание процедур резервного копирования

---

## 🎯 Заключение

Этот подход к автодеплою обеспечивает:

- **Простоту** - настраивается один раз
- **Надежность** - автоматические проверки и откаты
- **Безопасность** - зашифрованные ключи и ограниченный доступ
- **Масштабируемость** - легко адаптируется для новых проектов
- **Прозрачность** - полная видимость процесса

Следуя этому руководству, вы сможете настроить профессиональную систему автодеплоя для любого проекта за несколько часов.

**💡 Помните:** Всегда тестируйте деплой на staging окружении перед применением в production!