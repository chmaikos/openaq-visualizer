FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY batch_consumer.py .
CMD ["python", "batch_consumer.py"]