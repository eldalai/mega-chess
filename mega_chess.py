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


class NoTokenException(Exception):
    pass


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


REDIS_URL = os.environ.get('REDIS_URL')
if REDIS_URL:
    redis_pool = redis.from_url(url=REDIS_URL, db=0)
else:
    redis_pool = redis.Redis(host='redis', port=6379)

app = Quart(__name__)


@app.route('/')
async def home():
    return await render_template('index.html')


@app.route('/view')
async def view():
    return await render_template('view.html')


@app.route('/tournaments')
async def tournaments():
    context = {}
    context['tournaments'] = controller.tournament_manager.get_tournaments()
    return await render_template('tournaments.html', **context)


@app.route('/tournament/<tournament_id>')
async def tournament(tournament_id):
    context = {}
    context['tournament'] = controller.tournament_manager.get_tournament(tournament_id, with_boards=True)
    return await render_template('tournament.html', **context)


@app.route('/board-log/<board_id>')
async def board_log(board_id):
    context = {}
    context['board_log'] = controller.chess_manager.get_board_log(board_id)
    return await render_template('board_log.html', **context)


@app.route('/random')
async def random():
    return await render_template('random.html')


@app.route('/challenge')
async def challenge():
    return await render_template('challenge.html')


connected_websockets = set()
controller = Controller(redis_pool, app, connected_websockets)
# offline...
# controller = Controller(fakeredis.FakeStrictRedis(), app, connected_websockets)


@app.route('/register', methods=["POST"])
async def register():
    registration = await request.get_json()
    print(registration)
    try:
        controller.user_manager.register(**registration)
        return 'Register Ok!', 200
    except Exception as e:
        return 'Register ERROR! {}'.format(str(e)), 200


@app.route('/confirm_registration')
async def confirm_registration():
    registration_token = request.args.get('token')
    try:
        controller.user_manager.confirm_registration(registration_token)
        return 'Confirm Registration Ok!', 200
    except Exception as e:
        return 'Confirm Registration ERROR! {}'.format(str(e)), 200


@app.route('/token', methods=["POST"])
async def get_auth_token():
    registration = await request.get_json()
    print(registration)
    try:
        result = controller.user_manager.get_auth_token(**registration)
        return result, 200
    except Exception as e:
        return 'Register ERROR! {}'.format(str(e)), 200


@app.route('/ask_challenge', methods=["POST"])
async def ask_challenge():
    challenge = await request.get_json()
    print(challenge)
    try:
        await controller.challenge_with_auth_token(**challenge)
        return 'Challenge sent', 200
    except Exception as e:
        return 'Challenge ERROR! {}'.format(str(e)), 200


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


async def get_current_username(websocket):
    auth_token = websocket.args.get('authtoken')
    if not auth_token:
        raise NoTokenException()
    return await controller.user_manager.get_username_by_auth_token(auth_token)


@app.websocket('/service')
@collect_websocket
async def service(queue):
    # websocket.headers

    try:
        current_username = await get_current_username(websocket)
        queue.websocket = websocket
        websocket.queue = queue
        await controller.action_login(current_username, websocket)
        asyncio.create_task(broadcast(websocket, queue))
        while True:
            message = await websocket.receive()
            if message:
                app.logger.info(u'Receive from {}...{}'.format(websocket, queue))
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
    app.run(host="0.0.0.0", debug=True)
