FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY realtime_processor.py config.py .
CMD ["python", "realtime_processor.py"]