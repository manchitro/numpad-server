from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from pynput.keyboard import Controller, Key
import qrcode
import io
import base64
import uuid
import socket
import subprocess
import time
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")  # allow mobile browser
keyboard = Controller()


# Get your LAN IP
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


def start_ngrok(port=5000):
    # Start ngrok in the background
    subprocess.Popen(
        ["ngrok", "http", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    time.sleep(2)  # Give ngrok time to establish the tunnel

    # Try fetching the public URL
    try:
        tunnel_info = requests.get("http://localhost:4040/api/tunnels").json()
        public_url = tunnel_info["tunnels"][0]["public_url"]
        print(f"[+] ngrok tunnel active: {public_url}")
        return public_url
    except Exception as e:
        print("[-] Failed to get ngrok public URL:", e)
        return None


@app.route("/")
def index():
    session_id = str(uuid.uuid4())
    public_url = start_ngrok(port=5000)
    if not public_url:
        return "Failed to start ngrok", 500

    numpad_url = f"{public_url}/numpad?session={session_id}"

    # Generate QR code with the ngrok URL
    qr = qrcode.make(numpad_url)
    buffered = io.BytesIO()
    qr.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return render_template(
        "index.html", qr_data=img_str, session_id=session_id, numpad_url=numpad_url
    )


@app.route("/numpad")
def numpad():
    session_id = request.args.get("session")
    return render_template("numpad.html", session_id=session_id)


# Helper to simulate key press
def type_key(key):
    special_keys = {
        "Enter": Key.enter,
        "⌫": Key.backspace,
        "Backspace": Key.backspace,
        "Enter": Key.enter,
        # You can add more mappings like "Tab": Key.tab, etc.
    }

    if key in special_keys:
        keyboard.press(special_keys[key])
        keyboard.release(special_keys[key])
    else:
        keyboard.press(key)
        keyboard.release(key)


@socketio.on("key_press")
def handle_key_press(data):
    session = data.get("session")
    key = data.get("key")
    print(f"Session {session} pressed key: {key}")

    # Emulate key press on desktop
    try:
        type_key(key)
    except Exception as e:
        print(f"Error typing key '{key}': {e}")


if __name__ == "__main__":
    print("Server starting...")
    socketio.run(app, host="0.0.0.0", port=5000)
