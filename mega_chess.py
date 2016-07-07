# -*- coding: utf-8 -*-

"""
Chat Server
===========

This simple application uses WebSockets to run a primitive chat server.
"""
import os
import logging
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

from controller import Controller

REDIS_URL = os.environ['REDIS_URL']
REDIS_CHAN = 'chat'

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
redis = redis.from_url(REDIS_URL)

controller = Controller()


@app.route('/')
def hello():
    return render_template('index.html')


@sockets.route('/service')
def inbox(ws):
    app.logger.info(u'Receive from {}...'.format(ws))

    """Receives incoming chat messages"""
    while not ws.closed:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()

        app.logger.info(u'Processing message: {} from: {}'.format(message, ws))
        if message:
            controller.execute_message(ws, message)
