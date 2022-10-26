FROM python:3.10-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

WORKDIR /app/src

CMD ["python", "main.py"]