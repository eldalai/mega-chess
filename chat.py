
import os
import logging
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

REDIS_URL = os.environ['REDISCLOUD_URL']
REDIS_CHAN = 'chat'

app = Flask(__name__)
app.debug = True
sockets = Sockets(app)

redis = redis.from_url(REDIS_URL)
pubsub = redis.pubsub()

@sockets.route('/submit')
def inbox(ws):

    while True:
        message = ws.receive()

        if message:
            app.logger.info(u'Inserting message: {}'.format(message))
            redis.publish(REDIS_CHAN, message)

        gevent.sleep(0.1)


@sockets.route('/receive')
def outbox(ws):
    pubsub.subscribe(REDIS_CHAN)
    ws.send('hi')

    while True:
        # Message receipt
        for message in pubsub.listen():

            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: {}'.format(data))
                ws.send(data)

        gevent.sleep(0.1)

@app.route('/')
def hello():
    return render_template('index.html')