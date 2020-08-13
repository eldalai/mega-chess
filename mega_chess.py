# -*- coding: utf-8 -*-

"""
Chat Server
===========

This simple application uses WebSockets to run a primitive chat server.
"""
import os
import redis
import fakeredis
import gevent
from flask import Flask, render_template
from flask_sockets import Sockets

from controller import Controller

REDIS_URL = os.environ['REDIS_URL']

app = Flask(__name__)

if 'DEBUG' in os.environ:
    app.debug = True
    from gevent import monkey
    monkey.patch_all(thread=False)

sockets = Sockets(app)
# redis_pool = redis.from_url(url=REDIS_URL, db=0)
# controller = Controller(redis_pool, app)
controller = Controller(fakeredis.FakeStrictRedis(), app)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/view')
def view():
    return render_template('view.html')


@app.route('/random')
def random():
    return render_template('random.html')


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
