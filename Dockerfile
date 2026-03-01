FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода бота
COPY bot.py .

# Создание директории для данных
RUN mkdir -p /app/data

# Переменные окружения (будут переопределены при запуске)
ENV BOT_TOKEN=""
ENV GEMINI_API_KEY=""
ENV ADMIN_CHAT_ID="5309206282"

# Запуск бота
CMD ["python", "bot.py"]
