import asyncio
import websockets
import json
from pynput.keyboard import Controller, Key

keyboard = Controller()
sessions = {}


async def handle_connection(websocket, path):
    # Parse session from URL
    query = websocket.path.split("?")[-1]
    session_id = dict(qc.split("=") for qc in query.split("&")).get("session")

    print(f"Client connected with session: {session_id}")
    sessions[session_id] = websocket

    try:
        async for message in websocket:
            data = json.loads(message)
            key = data["key"]

            print(f"Received key: {key} for session: {session_id}")
            # Simulate keypress on the PC
            if key == "⌫":
                keyboard.press(Key.backspace)
                keyboard.release(Key.backspace)
            else:
                keyboard.press(key)
                keyboard.release(key)

    except websockets.ConnectionClosed:
        print(f"Session {session_id} disconnected.")
    finally:
        if session_id in sessions:
            del sessions[session_id]


async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 6789):
        print("WebSocket server running on ws://0.0.0.0:6789")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
