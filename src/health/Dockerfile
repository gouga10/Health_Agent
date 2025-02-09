# API Dockerfile
FROM python:3.12.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD python HealthFlow.py
