FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml main.py ./

RUN pip install --no-cache-dir . gunicorn

EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "main:app"]
