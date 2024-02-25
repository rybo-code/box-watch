FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN mkdir /app/aws_data

CMD ["python", "src/download_imagery.py"]
