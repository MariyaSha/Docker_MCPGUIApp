FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install mcp[cli]

CMD ["python3", "app.py"]