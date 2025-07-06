# 🔗 Пошаговое подключение GitHub к DigitalOcean App Platform

## 📋 Статус
- **GitHub репозиторий**: ✅ https://github.com/Timosan61/viralinstabot
- **DigitalOcean App**: ✅ `86f9f85d-e92d-40c1-a756-3b00435e0dd6` 
- **Переменные окружения**: ✅ Все настроены
- **GitHub Actions**: ✅ Настроены

## 🎯 Цель
Подключить GitHub репозиторий как источник кода для автоматического деплоя.

## 📝 Пошаговая инструкция

### Шаг 1: Откройте App Platform Console
```
https://cloud.digitalocean.com/apps/86f9f85d-e92d-40c1-a756-3b00435e0dd6
```

### Шаг 2: Перейдите к настройкам источника
1. В левой панели нажмите **Settings**
2. Найдите секцию **App-Level Settings**
3. Найдите **Source** и нажмите **Edit**

### Шаг 3: Подключите GitHub
1. В диалоге выбора источника выберите **GitHub**
2. Нажмите **Authorize with GitHub** 
3. В новом окне авторизуйтесь в GitHub (если нужно)
4. Разрешите доступ DigitalOcean к вашим репозиториям

### Шаг 4: Выберите репозиторий
1. **Repository**: `Timosan61/viralinstabot`
2. **Branch**: `main` 
3. **Source Directory**: `/` (корневая папка)
4. **Auto Deploy**: `ON` ✅

### Шаг 5: Настройте компонент бота
В секции **Components** убедитесь что настроено:
1. **Build Command**: `pip install --no-cache-dir -r requirements.txt`
2. **Run Command**: `python -m src.bot.main`
3. **Environment**: `python`
4. **HTTP Port**: `8080`

### Шаг 6: Сохраните и деплойте
1. Нажмите **Save**
2. Подтвердите изменения 
3. Нажмите **Deploy Changes**

## ✅ Проверка успешного подключения

После сохранения изменений:
1. В **Overview** должно отображаться: **Source: GitHub**
2. В **Activity** появится новый деплоймент
3. Статус деплоймента должен стать **Live**

## 🚀 Результат

После подключения GitHub:
- ✅ Каждый push в `main` ветку = автоматический деплой
- ✅ История деплойментов в DigitalOcean Console  
- ✅ GitHub Actions будут работать параллельно
- ✅ Rollback к предыдущим версиям одним кликом

## 🔧 Альтернативный способ через doctl CLI

Если у вас установлен doctl:

```bash
# Установка doctl (если нужно)
curl -sL https://github.com/digitalocean/doctl/releases/download/v1.104.0/doctl-1.104.0-linux-amd64.tar.gz | tar -xzv
sudo mv doctl /usr/local/bin

# Авторизация
doctl auth init

# Обновление app spec
doctl apps update 86f9f85d-e92d-40c1-a756-3b00435e0dd6 --spec .do/app.yaml
```

## 🆘 Если что-то пошло не так

1. **GitHub не отображается**: Проверьте авторизацию GitHub в настройках аккаунта DO
2. **Деплоймент падает**: Проверьте логи в **Runtime Logs**
3. **Переменные пропали**: Проверьте **Environment Variables** в настройках
4. **Build ошибки**: Проверьте **Build Logs** и requirements.txt

## 📞 Поддержка

- **DigitalOcean Docs**: https://docs.digitalocean.com/products/app-platform/
- **GitHub Integration**: https://docs.digitalocean.com/products/app-platform/how-to/manage-deployments/