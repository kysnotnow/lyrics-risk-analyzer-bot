# 🎵 Lyrics Risk Analyzer Bot

Telegram-бот для анализа текстов песен на потенциально рискованный контент.

## О проекте

Lyrics Risk Analyzer помогает артистам, лейблам и контент-менеджерам проверять тексты песен перед публикацией.

Бот анализирует:

- упоминания наркотиков;
- романтизацию наркотиков;
- насилие;
- преступную деятельность;
- экстремизм;
- самоповреждение;
- сексуальный контент;
- неоднозначные темы отношений.

Особое внимание уделяется метафорам и двойным смыслам.

---

## Как работает

1. Пользователь отправляет текст песни в Telegram.
2. LLM анализирует содержание.
3. Бот формирует структурированный отчёт.
4. Результат сохраняется в SQLite.

```
User
  ↓
Telegram Bot
  ↓
Analysis Service
  ↓
LLM (Ollama)
  ↓
JSON Validation
  ↓
SQLite
  ↓
Report
```

---

## Цветовая система

| Цвет | Значение |
|--------|--------|
| 🟢 GREEN | Риск не обнаружен |
| 🟡 YELLOW | Возможна неоднозначная трактовка |
| 🔴 RED | Высокий риск или прямое упоминание |

---

## Технологии

- Python 3.12
- aiogram 3
- SQLite
- Pydantic v2
- Ollama
- Docker

---

## Установка

### Клонирование

```bash
git clone https://github.com/kysnotnow/lyrics-risk-analyzer-bot.git
cd lyrics-risk-analyzer-bot
```

### Создание окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка

Создать `.env`

```env
BOT_TOKEN=your_token

LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL=llama3.1:8b
LLM_TIMEOUT_SECONDS=300


LOG_LEVEL=INFO
DATABASE_PATH=data/bot.db
MAX_LYRICS_LENGTH=8000
```

### Запуск

```bash
python -m app
```

---

## Статус проекта

### Реализовано

- Telegram-бот
- SQLite-хранилище
- Интеграция с Ollama
- Логирование
- Анализ текста
- Генерация отчёта

### В разработке

- Повышение стабильности JSON-ответов
- Улучшение анализа метафор
- Поддержка нескольких моделей
- Веб-интерфейс

---

## Пример использования

Отправить текст песни:

```
In the back of my mind
I killed you
And I didn't even regret it
```

Получить отчёт:

```
Risk: YELLOW

Category:
Violence

Literal meaning:
Direct statement about killing.

Metaphorical meaning:
Possible emotional detachment from a person.

Recommendation:
Requires additional review.
```

---

## Лицензия

MIT
