import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

def start_web_server_thread():
    web_thread = Thread(target=run_web_server)
    web_thread.daemon = True
    web_thread.start()
