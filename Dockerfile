FROM python:3.11-slim-bookworm

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./.env /code/.env
COPY ./servers_api.json /code/servers_api.json
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["python", "app/bot.py"]
