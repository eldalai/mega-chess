
import os
import logging
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

REDIS_URL = os.environ['REDISCLOUD_URL']
REDIS_CHAN = 'chat'

app = Flask(__name__)
# app.debug = True
sockets = Sockets(app)

redis = redis.from_url(REDIS_URL)



class ChatBackend(object):
    def __init__(self):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHAN)

    def register(self, client):
        self.clients.append(client)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: {}'.format(data))
                yield data

    def run(self):
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(client.send, data)


    def start(self):
        gevent.spawn(self.run)


def hmm(x):
    print x

chats = ChatBackend()
# chats.register(hmm)
chats.start()
# exit()
# # chats.start()



@sockets.route('/submit')
def inbox(ws):

    while ws.socket is not None:
        gevent.sleep(0.1)
        message = ws.receive()

        if message:
            app.logger.info(u'Inserting message: {}'.format(message))
            redis.publish(REDIS_CHAN, message)



@sockets.route('/receive')
def outbox(ws):
    # stream = chats.gen()
    chats.register(ws)



    while ws.socket is not None:
    #     ws.
    #     for message in stream:
    #         ws.send(stream)
        gevent.sleep()



# @sockets.route('/receive')
# def outbox(ws):
#     chats.register(ws)
#     pubsub.subscribe(REDIS_CHAN)

#     while ws.socket is not None:
#         gevent.sleep(0.1)
#         # Message receipt
#         for message in pubsub.listen():

#             data = message.get('data')
#             if message['type'] == 'message':
#                 app.logger.info(u'Sending message: {}'.format(data))
#                 ws.send(data)

#         # gevent.sleep(0.1)

@app.route('/')
def hello():
    return render_template('index.html')