FROM python:latest

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app
EXPOSE 8080

CMD ["python", "main.py"]