# Використовуємо легкий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Запобігаємо створенню .pyc файлів та вмикаємо логування в реальному часі
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо проект
COPY . .

# Створюємо папку для медіа
RUN mkdir -p media

# Запуск
CMD ["python", "-m", "src.bot"]