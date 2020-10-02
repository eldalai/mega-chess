FROM python:3

RUN apt-get update -y && \
    apt-get install -y git

ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_APP=mega_chess.py
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 5000

COPY . /app

ENTRYPOINT [ "python" ]

CMD ["mega_chess.py"]