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
    uri = "ws://127.0.0.1:5000/service?authtoken={}".format(auth_token)
    async with websockets.connect(uri) as websocket:
        await send(websocket, 'login', {})
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
                print('retry')


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        auth_token = sys.argv[1]
        asyncio.get_event_loop().run_until_complete(start(auth_token))
    else:
        print('please provide your auth_token')
