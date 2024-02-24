FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ app/src/
COPY tests/ app/tests/
RUN mkdir /app/aws_data

CMD ["python", "/app/src/download_imagery.py"]
