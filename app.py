#!/usr/bin/env python3
# https://github.com/ReturnOfTheLast/p3_management_interface

from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from dotenv import load_dotenv
from os import environ
from bson import json_util
from bson import ObjectId
import requests
import json

load_dotenv()

app: Flask = Flask(__name__)
mongo: MongoClient = MongoClient(environ['MONGO_URI'])
db_management: Database = mongo['iotwarden-management']
users_col: Collection = db_management['users']

db_system: Database = mongo['iotwarden']
whiteblacklist: Collection = db_system['whiteblacklist']


# --- [ Frontend ]
@app.get('/')
def front_index():
    users: Cursor = users_col.find()
    whiteblacklist_entries: Cursor = whiteblacklist.find()
    whitelisted = []
    blacklisted = []

    for entry in whiteblacklist_entries:
        if entry['allowed']:
            whitelisted.append(entry)
        else:
            blacklisted.append(entry)

    return render_template(
        'index.html',
        users=users,
        whiteblacklists=[
            ("Whitelisted", whitelisted),
            ("Blacklisted", blacklisted)
        ]
    )


@app.get('/mongo')
def front_mongo():
    return render_template('mongo.html')


@app.get('/redis')
def front_redis():
    return render_template('redis.html')


# --- [ API ]
@app.get('/api/users')
def api_get_users():
    args = request.args
    if args.get('id', None):
        users: Cursor = users_col.find_one({'_id': ObjectId(args['id'])})
    else:
        users: Cursor = users_col.find()

    return jsonify(json.loads(json_util.dumps(users)))


@app.post('/api/users/add')
def api_add_user():
    req_json = request.get_json()
    if not req_json.get('name', None):
        return jsonify({
            "success": False,
            "payload": {},
            "error": {
                "code": 400,
                "message": "User must have a name"
            }
        }), 400

    oid: ObjectId = users_col.insert_one(req_json).inserted_id
    return jsonify({
        "success": True,
        "payload": {
            "id": str(oid)
        }
    })


@app.post('/api/notify')
def api_notify():
    req_json = request.get_json()
    if not req_json.get('message', None):
        return jsonify({
            "success": False,
            "payload": {},
            "error": {
                "code": 400,
                "message": "A message must be set"
            }
        }), 400

    message_count: int = 0
    for user in users_col.find():
        token = user.get('gotify_token', None)
        if token:
            requests.post(
                f'https://gotify.osiriz.xyz/message?token={token}',
                json={
                    'message': req_json.get('message'),
                    'priority': req_json.get('priority', 0),
                    'title': req_json.get('title', 'IoT-Warden')
                }
            )
            message_count += 1

    return jsonify({
        "success": True,
        "payload": {
            "message_count": message_count
        }
    })


if __name__ == '__main__':
    app.run('0.0.0.0', 8080, debug=True)
