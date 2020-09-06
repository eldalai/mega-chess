import asyncio
import json
from random import randint
import sys
import websockets


async def send(websocket, action, data):
    message = json.dumps(
        {
            'action': action,
            'data': data,
        }
    )
    print(message)
    await websocket.send(message)


async def start(auth_token):
    uri = "ws://mega-chess-qa.herokuapp.com/service?authtoken={}".format(auth_token)
    while True:
        print('connection to {}'.format(uri))
        async with websockets.connect(uri) as websocket:
            await send(websocket, 'login', {})
            await play(websocket)


async def play(websocket):
    while True:
        try:
            response = await websocket.recv()
            print(f"< {response}")
            data = json.loads(response)
            if data['action'] == 'update_user_list':
                pass
            if data['action'] == 'gameover':
                pass
            if data['action'] == 'ask_challenge':
                await send(
                    websocket,
                    'accept_challenge',
                    {
                        'board_id': data['data']['board_id'],
                    },
                )
            if data['action'] == 'your_turn':
                await send(
                    websocket,
                    'move',
                    {
                        'board_id': data['data']['board_id'],
                        'turn_token': data['data']['turn_token'],
                        'from_row': randint(0, 15),
                        'from_col': randint(0, 15),
                        'to_row': randint(0, 15),
                        'to_col': randint(0, 15),
                    },
                )

        except Exception as e:
            print('error {}'.format(str(e)))
            break  # force login again


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        auth_token = sys.argv[1]
        asyncio.get_event_loop().run_until_complete(start(auth_token))
    else:
        print('please provide your auth_token')
