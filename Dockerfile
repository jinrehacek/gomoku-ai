FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY gomoku /app/gomoku

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "gomoku", "--serve", "--host", "0.0.0.0", "--port", "8000"]
