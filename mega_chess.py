# -*- coding: utf-8 -*-

"""
Chat Server
===========

This simple application uses WebSockets to run a primitive chat server.
"""
import os
import redis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

from controller import Controller

REDIS_URL = os.environ['REDIS_URL']
REDIS_DB = os.environ['REDIS_DB']

app = Flask(__name__)
app.debug = 'DEBUG' in os.environ

sockets = Sockets(app)
redisPool = redis.from_url(url=REDIS_URL, db=0)
controller = Controller(redisPool)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/view')
def view():
    return render_template('view.html')


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
