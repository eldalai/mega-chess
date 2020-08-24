# -*- coding: utf-8 -*-

"""
Chat Server
===========

This simple application uses WebSockets to run a primitive chat server.
"""
import os
from logging.config import dictConfig
from mock import wraps
import asyncio

import redis
import fakeredis
from quart import Quart, websocket, render_template, request

from controller import Controller


dictConfig({
    'version': 1,
    'loggers': {
        'quart.app': {
            'level': 'INFO',
        },
    },
})

from logging import getLogger
from quart.logging import default_handler



REDIS_URL = os.environ['REDIS_URL']

app = Quart(__name__)

# if 'DEBUG' in os.environ:
#     app.debug = True
#     from gevent import monkey
#     monkey.patch_all(thread=False)

# sockets = Sockets(app)
redis_pool = redis.from_url(url=REDIS_URL, db=0)
# controller = Controller(fakeredis.FakeStrictRedis(), app)


@app.route('/')
async def home():
    return await render_template('index.html')


@app.route('/view')
async def view():
    return await render_template('view.html')


@app.route('/tournaments')
async def tournaments():
    return await render_template('tournaments.html')


@app.route('/random')
async def random():
    return await render_template('random.html')

connected_websockets = set()
controller = Controller(redis_pool, app, connected_websockets)


@app.route('/register', methods=["POST"])
async def register():
    registration = await request.get_json()
    print(registration)
    try:
        result = controller.user_manager.register(**registration)
        return 'Register Ok!', 200
    except Exception as e:
        return 'Register ERROR! {}'.format(str(e)), 200


@app.route('/token', methods=["POST"])
async def get_auth_token():
    registration = await request.get_json()
    print(registration)
    try:
        result = controller.user_manager.get_auth_token(**registration)
        return result, 200
    except Exception as e:
        return 'Register ERROR! {}'.format(str(e)), 200


def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        queue = asyncio.Queue()
        connected_websockets.add(queue)
        try:
            return await func(queue, *args, **kwargs)
        finally:
            connected_websockets.remove(queue)
    return wrapper


@app.websocket('/service')
@collect_websocket
async def service(queue):
    # websocket.headers

    try:
        queue.websocket = websocket
        websocket.queue = queue
        asyncio.create_task(broadcast(websocket, queue))
        while True:
            message = await websocket.receive()
            # await websocket.send("Receive ")
            if message:
                app.logger.info(u'Receive from {}...{}'.format(websocket, queue))
                # import ipdb; ipdb.set_trace()
                app.logger.info(
                    u'Processing message: {} from: {}'.format(message, websocket),
                )
                asyncio.create_task(controller.execute_message(websocket, message))

    except asyncio.CancelledError:
        # Handle disconnect
        raise


async def broadcast(websocket, queue):
    try:
        while True:
            if hasattr(websocket, 'username'):
                queue.username = websocket.username
            data = await queue.get()
            await websocket.send(data)
    except asyncio.CancelledError:
        # Handle disconnect
        raise


if __name__ == '__main__':
    app.run()