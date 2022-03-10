from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
  return "Well, you cann tell by the way I use my walk I'm a woman's man, no time to talk"

def run():
  app.run(host='0.0.0.0', port=8080)

def stayin_alive():
  t = Thread(target=run)
  t.start()
