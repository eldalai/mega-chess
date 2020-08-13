FROM python:3

RUN apt-get update -y && \
    apt-get install -y git

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

CMD [ "mega_chess.py" ]