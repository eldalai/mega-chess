import asyncio
import websockets


async def hello():
    uri = "ws://127.0.0.1:5000/service"
    while True:    
        try:
            async with websockets.connect(uri) as websocket:
                name = input("What's your name? ")

                await websocket.send(name)
                print(f"> {name}")

                greeting = await websocket.recv()
                print(f"< {greeting}")
        except Exception as e:
            print('retry')


asyncio.get_event_loop().run_until_complete(hello())
