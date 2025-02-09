# Streamlit Dockerfile
FROM python:3.12.8-slim

WORKDIR /app


RUN pip install streamlit requests

COPY . .

CMD streamlit run streamlit.py
