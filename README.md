# Instagram Viral Bot

Telegram-бот для анализа вирусных Instagram Reels с использованием AI и Apify.

## Возможности

- 🎯 Анализ вирусных Reels по заданным критериям
- 🤖 Умный агент на базе GPT-4-mini для извлечения параметров
- 🎤 Поддержка голосовых сообщений (Whisper API)
- 📊 Генерация мобильных PDF-отчетов
- 💰 Предварительный расчет стоимости анализа
- 🌍 Гео-таргетинг по локации пользователей

## Технологии

- Python 3.11+
- aiogram 3.x - Telegram Bot API
- OpenAI API (GPT-4-mini, Whisper)
- Apify MCP Server - интеграция через stdio
- WeasyPrint - генерация PDF
- SQLite + SQLAlchemy - хранение данных

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/instagram-viral-bot.git
cd instagram-viral-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте `.env.example` в `.env` и заполните необходимые ключи:
```bash
cp .env.example .env
```

5. Установите Apify MCP Server:
```bash
npm install -g @apify/actors-mcp-server
```

## Запуск

### Локальный запуск
```bash
python -m src.bot.main
```

### Docker
```bash
docker-compose up -d
```

## Конфигурация

Основные настройки находятся в `config/bot.yml`:
- Токены API
- Лимиты и таймауты
- Параметры моделей AI

## Использование

1. Запустите бота командой `/start`
2. Нажмите "🔥 Вирусные ролики"
3. Отправьте текстовый или голосовой запрос
4. Ответьте на уточняющие вопросы (если потребуется)
5. Подтвердите запуск анализа после просмотра цены
6. Получите PDF-отчет с результатами

## Примеры запросов

- "Вирусные видео про фитнес за последние 7 дней"
- "Популярные reels по йоге в России"
- "Топ видео по кулинарии за месяц"

## Структура проекта

```
instagram-viral-bot/
├── config/           # Конфигурационные файлы
├── data/            # База данных и отчеты
├── templates/       # HTML-шаблоны для PDF
├── src/
│   ├── agent/       # QueryAgent с AI
│   ├── bot/         # Telegram bot handlers
│   ├── services/    # Внешние интеграции
│   ├── domain/      # Модели данных
│   ├── storage/     # Работа с БД
│   └── utils/       # Вспомогательные функции
└── tests/           # Тесты
```

## Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=src --cov-report=html

# Только unit-тесты
pytest tests/unit/

# E2E тесты
pytest tests/e2e/
```

## Лицензия

MIT License