# Расчёты аналитики Instagram

## Расчёт коэффициента вовлечённости (ER)

### Основная формула (используется в боте)
```python
engagement_rate = ((лайки + комментарии) / просмотры) * 100
```

### Пример расчёта
Для Reel с параметрами:
- Просмотры: 4,567
- Лайки: 1,523  
- Комментарии: 342

```
ER = ((1,523 + 342) / 4,567) * 100
ER = (1,865 / 4,567) * 100
ER = 0.4084 * 100
ER = 40.84%
```

### Почему эта формула?
- **ER на основе просмотров** более точен для Reels, так как показывает процент зрителей, которые взаимодействовали с контентом
- Instagram Reels приоритизирует просмотры как основную метрику
- Эта формула соответствует тому, как алгоритм Instagram оценивает эффективность контента

## Другие расчёты

### Средний коэффициент вовлечённости
```python
средний_er = sum(reel.engagement_rate for reel in reels) / len(reels)
```

### Общие метрики
```python
общие_просмотры = sum(reel.views for reel in reels)
общие_лайки = sum(reel.likes for reel in reels)
общие_комментарии = sum(reel.comments for reel in reels)
```

### Оценка просмотров (для не-Reels)
Когда `videoViewCount` недоступен:
```python
оценочные_просмотры = количество_лайков * 10
```
Это предполагает, что примерно 10% зрителей ставят лайк (средний показатель по индустрии).

## Форматирование метрик

### Форматирование чисел
- Числа > 1,000,000: "1.2M"
- Числа > 1,000: "12.3K"  
- Числа < 1,000: "999"

### Форматирование процентов
- Всегда показываются с одним знаком после запятой: "40.8%"
- Округление по стандартным правилам

## Примечания по качеству данных

1. **Обработка отсутствующих данных**
   - Если просмотры = 0, ER устанавливается в 0%
   - Отсутствующее количество комментариев по умолчанию = 0
   - Отсутствующее количество лайков по умолчанию = 0

2. **Обработка выбросов**
   - ER > 100% ограничивается 100%
   - Отрицательные значения устанавливаются в 0

3. **Фильтрация по времени**
   - Включаются только посты в запрошенном периоде
   - Часовой пояс: UTC (по умолчанию в Instagram API)

## Бизнес-логика

### Выбор размера выборки
- **5 Reels**: Быстрый обзор, минимальная стоимость
- **7 Reels**: Сбалансированный анализ (рекомендуется)
- **10 Reels**: Комплексный анализ

### Выбор периода  
- **3 дня**: Последние тренды, вирусный контент
- **7 дней**: Недельная производительность (по умолчанию)
- **14 дней**: Более широкие паттерны

### Логика сортировки
Reels сортируются по коэффициенту вовлечённости (сначала самые высокие), чтобы показать наиболее эффективный контент в начале отчёта.