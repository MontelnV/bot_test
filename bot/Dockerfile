FROM python:3.9-slim-buster

WORKDIR /code

COPY ./bot/requirements.txt /code/requirements.txt
COPY ./app/.env /code/.env

RUN pip install --no-cache-dir -r /bot/requirements.txt

COPY ./bot /code/bot

CMD ["python", "bot/bot.py"]
