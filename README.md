# AI Centers Sales Bot 🤖

Telegram-бот продажник для AI Centers — ведёт клиента от интереса до оплаты через Telegram Stars.

## 🎯 Функционал

### Основные возможности
- ✅ **Приветствие и меню** — `/start` показывает главное меню
- ✅ **Демо** — перенаправление на @aicenters_demo_bot
- ✅ **Тарифы** — красивое отображение 4 тарифных планов
- ✅ **Форма связи** — сбор заявок с сохранением в JSON
- ✅ **FAQ** — ответы на частые вопросы
- ✅ **Оплата через Telegram Stars** — встроенная оплата
- ✅ **Онбординг** — сбор данных о бизнесе после оплаты
- ✅ **AI-чат** — ответы через Gemini 2.5 Flash на любые вопросы
- ✅ **Уведомления админу** — при новой заявке и оплате

### Тарифы
| Тариф | Цена | Stars | Особенности |
|-------|------|-------|-------------|
| **Starter** | $15/мес | 150 ⭐ | Базовый Telegram бот, 1 ниша, 500 сообщений |
| **Business** | $49/мес | 500 ⭐ | Telegram + сайт, любая ниша, 3000 сообщений, аналитика |
| **Pro** | $99/мес | 1000 ⭐ | Безлимит, WhatsApp, кастомизация, менеджер |
| **Enterprise** | $149/мес | 1500 ⭐ | Голосовой AI, CRM, API, SLA 99.9% |

## 🛠 Стек технологий
- **Python 3.11+**
- **aiogram 3.7** — асинхронный Telegram Bot API
- **Gemini 2.5 Flash** — AI для чата с клиентами
- **FSM** — state management для форм
- **JSON** — хранение лидов и данных онбординга

## 📦 Установка

### 1. Клонирование и установка зависимостей
```bash
cd /root/.openclaw/workspace/ai_centers_platform/sales_bot/
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
Создайте файл `.env`:
```env
BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_api_key
ADMIN_CHAT_ID=5309206282
```

### 3. Запуск
```bash
python bot.py
```

## 🐳 Docker

### Сборка образа
```bash
docker build -t ai-centers-sales-bot .
```

### Запуск контейнера
```bash
docker run -d \
  --name sales-bot \
  -e BOT_TOKEN="your_token" \
  -e GEMINI_API_KEY="your_key" \
  -e ADMIN_CHAT_ID="5309206282" \
  -v $(pwd)/data:/app/data \
  ai-centers-sales-bot
```

### Или с docker-compose
```yaml
version: '3.8'
services:
  sales-bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ADMIN_CHAT_ID=5309206282
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

## 📁 Структура данных

### leads.json — Заявки
```json
[
  {
    "name": "Иван",
    "business": "Кафе Сытый Кот",
    "niche": "🍽 Ресторан",
    "contact": "+79001234567",
    "user_id": 123456789,
    "username": "ivan_cat",
    "timestamp": "2026-03-01T08:00:00"
  }
]
```

### onboarding.json — Данные онбординга
```json
[
  {
    "plan": "business",
    "business_name": "Салон Красота",
    "niche": "💇 Салон",
    "description": "Женский салон красоты. Стрижки, окрашивание, маникюр.",
    "user_id": 987654321,
    "username": "salon_beauty",
    "timestamp": "2026-03-01T09:00:00"
  }
]
```

## 🎨 Пример диалога

```
👤 Пользователь: /start

🤖 Бот:
👋 **Привет! Я AI Centers** — мы создаём умных AI-ассистентов для бизнеса за 24 часа.
Что вас интересует?
[🎯 Демо] [💰 Тарифы] [📞 Связаться] [❓ FAQ]

👤 Пользователь: [нажимает 💰 Тарифы]

🤖 Бот:
💰 **Выберите тариф:**

**Starter — $15/мес**
✓ Telegram бот
✓ 1 ниша
✓ 500 сообщений/мес
...
[Подключить Starter] [Подключить Business ⭐] ...

👤 Пользователь: [нажимает Подключить Business]

🤖 Бот: [создаёт invoice на 500 Stars]

👤 Пользователь: [оплачивает]

🤖 Бот:
🎉 **Спасибо за покупку!**
Вы подключили тариф **Business**.
**Название вашего бизнеса?**

... [онбординг] ...
```

## 🚀 Деплой на Railway

### 1. Railway CLI
```bash
railway login
railway init
railway up
```

### 2. Environment Variables в Railway
```
BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
ADMIN_CHAT_ID=5309206282
```

### 3. Добавьте volume для данных
В Railway настройках добавьте:
- Volume path: `/app/data`

## 📊 Мониторинг

Бот логирует все действия:
- ✅ Новые пользователи
- ✅ Заявки
- ✅ Оплаты
- ✅ Ошибки

Логи можно смотреть через:
```bash
# Docker
docker logs -f sales-bot

# Railway
railway logs
```

## 🔐 Безопасность

- ✅ Все токены в environment variables
- ✅ Данные хранятся локально в JSON
- ✅ Уведомления админу о всех действиях
- ✅ Валидация платежей через pre_checkout_query

## 📞 Поддержка

- **Telegram**: @aicenters_hub_bot
- **Email**: support@aicenters.com
- **Admin ID**: 5309206282

## 📝 TODO / Roadmap

- [ ] Подключение базы данных (PostgreSQL)
- [ ] Админ-панель для управления тарифами
- [ ] A/B тестирование текстов
- [ ] Аналитика воронки продаж
- [ ] Интеграция с платёжными системами (Stripe, PayPal)
- [ ] Многоязычность (автоопределение языка)
- [ ] Промокоды и скидки

## 📄 Лицензия

MIT License - используйте как хотите!

---

**Сделано с ❤️ для AI Centers**
