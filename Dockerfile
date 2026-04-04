FROM python:3.13-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY gomoku ./gomoku

# Install dependencies
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "gomoku", "--serve", "--host", "0.0.0.0", "--port", "8000"]
