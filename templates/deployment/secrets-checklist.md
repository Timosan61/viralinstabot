# 🔐 GitHub Secrets Setup Checklist

## 📋 Обязательные секреты для автодеплоя

### 1. SSH подключение к серверу

#### `SERVER_HOST` или `DROPLET_HOST`
```
# IP адрес или домен вашего сервера
123.456.789.012
# или
myserver.example.com
```

#### `SERVER_USER` или `DROPLET_USER`
```
# Имя пользователя на сервере
ubuntu
# или
root
# или
deploy
```

#### `SERVER_SSH_KEY` или `DROPLET_SSH_KEY`
```
# Приватный SSH ключ (ПОЛНОСТЬЮ, включая заголовки)
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAA...
[весь ключ]
-----END OPENSSH PRIVATE KEY-----
```

### 2. Опциональные секреты

#### `APP_DIR`
```
# Путь к директории приложения на сервере
/home/ubuntu/myapp
# или
/opt/myapp
```

#### `GRAFANA_PASSWORD`
```
# Пароль для Grafana (если используете мониторинг)
your-secure-password
```

## 🛠 Создание SSH ключей

### Шаг 1: Генерация ключа на сервере

```bash
# На вашем сервере выполните:
ssh-keygen -t ed25519 -f ~/.ssh/github_actions_deploy -N "" -C "github-actions-deploy@$(hostname)"

# Вывод приватного ключа (скопируйте ВЕСЬ вывод для GitHub Secrets)
cat ~/.ssh/github_actions_deploy

# Вывод публичного ключа
cat ~/.ssh/github_actions_deploy.pub
```

### Шаг 2: Добавление публичного ключа

```bash
# Добавление публичного ключа в authorized_keys
cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys

# Установка правильных прав доступа
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/github_actions_deploy
chmod 644 ~/.ssh/github_actions_deploy.pub
```

### Шаг 3: Тестирование SSH ключа

```bash
# Тест подключения с новым ключом
ssh -i ~/.ssh/github_actions_deploy $(whoami)@localhost echo "SSH working!"

# Если работает, удалите тестовую строку из known_hosts
ssh-keygen -R localhost
```

## 🔧 Настройка GitHub Secrets

### Путь в GitHub
1. Откройте ваш репозиторий на GitHub
2. Перейдите в **Settings** → **Secrets and variables** → **Actions**
3. Нажмите **New repository secret**

### Добавление секретов

#### 1. SERVER_HOST
- **Name**: `SERVER_HOST` (или `DROPLET_HOST`)
- **Secret**: IP адрес вашего сервера

#### 2. SERVER_USER
- **Name**: `SERVER_USER` (или `DROPLET_USER`)  
- **Secret**: имя пользователя на сервере

#### 3. SERVER_SSH_KEY
- **Name**: `SERVER_SSH_KEY` (или `DROPLET_SSH_KEY`)
- **Secret**: ПОЛНЫЙ приватный SSH ключ (включая заголовки)

⚠️ **Важно**: Вставляйте приватный ключ ПОЛНОСТЬЮ, включая строки:
```
-----BEGIN OPENSSH PRIVATE KEY-----
```
и
```
-----END OPENSSH PRIVATE KEY-----
```

## 🔍 Проверка настройки

### Тест через GitHub Actions

Создайте тестовый workflow файл `.github/workflows/test-connection.yml`:

```yaml
name: Test SSH Connection

on: workflow_dispatch

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - name: Setup SSH
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SERVER_SSH_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh-keyscan -H ${{ secrets.SERVER_HOST }} >> ~/.ssh/known_hosts
        
    - name: Test SSH
      run: |
        ssh ${{ secrets.SERVER_USER }}@${{ secrets.SERVER_HOST }} "echo 'SSH connection successful!' && hostname && whoami"
```

Запустите этот workflow в разделе **Actions** → **Test SSH Connection** → **Run workflow**.

### Ручное тестирование на сервере

```bash
# Проверка файла authorized_keys
cat ~/.ssh/authorized_keys | grep "github-actions"

# Проверка прав доступа
ls -la ~/.ssh/

# Тест SSH подключения
ssh -i ~/.ssh/github_actions_deploy $(whoami)@$(hostname) "echo 'Test successful'"
```

## 🚨 Устранение проблем

### Ошибка "Permission denied (publickey)"

1. **Проверьте права доступа на файлы:**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/github_actions_deploy
   ```

2. **Проверьте содержимое authorized_keys:**
   ```bash
   cat ~/.ssh/authorized_keys | grep "github-actions"
   ```

3. **Проверьте правильность ключа в GitHub Secrets:**
   - Убедитесь, что скопировали ВЕСЬ приватный ключ
   - Проверьте, что нет лишних пробелов в начале/конце

### Ошибка "Host key verification failed"

```bash
# Очистите known_hosts и добавьте хост заново
ssh-keyscan -H YOUR_SERVER_IP >> ~/.ssh/known_hosts
```

### Ошибка "error in libcrypto"

Это означает, что приватный ключ поврежден или неполный:
1. Пересоздайте SSH ключ
2. Убедитесь, что копируете ПОЛНЫЙ ключ в GitHub Secrets
3. Проверьте, что нет лишних символов

## 🔄 Ротация ключей

### Каждые 6-12 месяцев рекомендуется:

1. **Создать новый SSH ключ:**
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/github_actions_deploy_new -N ""
   ```

2. **Добавить новый ключ в authorized_keys:**
   ```bash
   cat ~/.ssh/github_actions_deploy_new.pub >> ~/.ssh/authorized_keys
   ```

3. **Обновить GitHub Secrets** новым приватным ключом

4. **Протестировать деплой** с новым ключом

5. **Удалить старый ключ** из authorized_keys:
   ```bash
   # Отредактируйте файл и удалите строку со старым ключом
   nano ~/.ssh/authorized_keys
   ```

## ✅ Финальная проверка

- [ ] SSH ключ создан на сервере
- [ ] Публичный ключ добавлен в authorized_keys
- [ ] Права доступа настроены правильно
- [ ] Все 3 обязательных секрета добавлены в GitHub
- [ ] Тестовый workflow прошел успешно
- [ ] Основной деплой работает

🎉 **Готово!** Теперь ваш автодеплой должен работать корректно!