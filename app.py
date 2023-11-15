#!/usr/bin/env python3
# https://github.com/ReturnOfTheLast/p3_management_interface

from flask import Flask, render_template, request, jsonify
from gotify import Gotify
import json

with open('config.json', 'r') as fp:
    config: dict = json.load(fp)

gotifies: list[Gotify] = list()
for token in config['gotify_tokens']:
    gotifies.append(Gotify(
        base_url=config['gotify_url'],
        app_token=token
    ))

app = Flask(__name__)


# --- [ Frontend ]
@app.get('/')
def index():
    return render_template('index.html')


@app.get('/mongo')
def mongo():
    return render_template('mongo.html')


@app.get('/redis')
def redis():
    return render_template('redis.html')


# --- [ API ]
@app.post('/api/notify')
def notify():
    req_json = request.get_json()
    for gotify in gotifies:
        gotify.create_message(
            req_json["message"],
            title=req_json["title"],
            priority=req_json["priority"]
        )
    return jsonify({
        "number_of_messages": len(gotifies)
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 8080)
