"""Project constants."""

# Currency
USD_TO_RUB = 90.0
PRICE_MULTIPLIER = 2  # 100% markup

# Limits
MAX_REQUESTS_PER_USER = 10
MAX_PDF_SIZE_MB = 5
REELS_LIMIT = 5  # Top 5 reels per analysis

# Time periods
PERIOD_7_DAYS = 7
PERIOD_30_DAYS = 30
ALLOWED_PERIODS = [PERIOD_7_DAYS, PERIOD_30_DAYS]

# Geo locations
GEO_RUSSIA = "RU"
GEO_USA = "US"
GEO_WORLD = "WORLD"
DEFAULT_GEO = GEO_RUSSIA

# QueryAgent
MAX_CLARIFICATION_ITERATIONS = 3
AGENT_TIMEOUT_SECONDS = 30

# Telegram
BOT_COMMANDS = {
    "start": "Начать работу с ботом",
    "help": "Показать справку",
    "cancel": "Отменить текущую операцию"
}

# Buttons
BTN_VIRAL_VIDEOS = "🔥 Вирусные ролики"
BTN_HELP = "❓ Помощь"
BTN_NEW_ANALYSIS = "🔄 Новый анализ"
BTN_CONFIRM_RUN = "✅ Запустить"
BTN_EDIT_QUERY = "✏️ Изменить"

# Messages
MSG_WELCOME = """
👋 Привет! Я помогу найти вирусные Instagram Reels по вашему запросу.

Что я умею:
• Анализировать популярные Reels по теме
• Определять критерии вирусности
• Создавать детальные PDF-отчеты

Нажмите кнопку ниже, чтобы начать!
"""

MSG_HELP = """
📖 Как пользоваться ботом:

1. Нажмите "🔥 Вирусные ролики"
2. Отправьте текстовый или голосовой запрос
3. Ответьте на уточняющие вопросы
4. Подтвердите запуск анализа
5. Получите PDF-отчет

Примеры запросов:
• "Фитнес за последние 7 дней"
• "Йога в России за месяц"
• "Популярные рецепты"

💡 Подсказка: можете сразу указать период (7 или 30 дней) и страну!
"""

MSG_PROCESSING = "⏳ Обрабатываю ваш запрос..."
MSG_ANALYZING = "🔍 Анализирую Reels..."
MSG_GENERATING_PDF = "📄 Генерирую отчет..."
MSG_ERROR = "❌ Произошла ошибка. Попробуйте еще раз."

# Apify
APIFY_ACTOR_ID = "apify/instagram-reel-scraper"
APIFY_SORT_BY = "TOP"
APIFY_RESULTS_TYPE = "posts"
APIFY_SEARCH_TYPE = "hashtag"