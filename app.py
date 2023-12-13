#!/usr/bin/env python3
# https://github.com/ReturnOfTheLast/p3_management_interface

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for
)
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from dotenv import load_dotenv
from os import environ
from bson import json_util
from bson import ObjectId
from redis import Redis
import requests
import json

load_dotenv()

app: Flask = Flask(__name__)
mongo: MongoClient = MongoClient(environ['MONGO_URI'])
db_management: Database = mongo['iotwarden-management']
users_col: Collection = db_management['users']

db_system: Database = mongo['iotwarden']
whiteblacklist: Collection = db_system['whiteblacklist']

redis_client: Redis = Redis(environ['REDIS_HOST'], environ['REDIS_PORT'])


# --- [ Frontend ]
@app.get('/')
def front_index():
    users: Cursor = users_col.find()
    mongo_wbl_entries: Cursor = whiteblacklist.find()
    mongo_wl = []
    mongo_bl = []
    redis_wl = []
    redis_bl = []

    for entry in mongo_wbl_entries:
        if entry['allowed']:
            mongo_wl.append(entry)
        else:
            mongo_bl.append(entry)

    for key in redis_client.scan_iter():
        str_key = key.decode()
        if str_key[:5] == "list_":
            if redis_client.get(key) == 'white':
                redis_wl.append(str_key[5:])
            else:
                redis_bl.append(str_key[5:])

    return render_template(
        'index.html',
        users=users,
        mongo_wbl=[
            ("Whitelisted", mongo_wl),
            ("Blacklisted", mongo_bl)
        ],
        redis_wbl=[
            ('Whitelisted', redis_wl),
            ("Blacklisted", redis_bl)
        ]
    )


@app.get('/mongo')
def front_mongo():
    hostname = request.headers.get('Host').split(':')[0]
    return render_template('mongo.html', hostname=hostname)


@app.get('/redis')
def front_redis():
    hostname = request.headers.get('Host').split(':')[0]
    return render_template('redis.html', hostname=hostname)


@app.route('/users/add', methods=['GET', 'POST'])
def front_add_user():
    if request.method == 'POST':
        data = request.form
        hostname = request.headers.get('Host').split(':')

        requests.get(
            f"http://{hostname}{url_for('api_add_user')}",
            json={
                'name': data['name'],
                'gotify_token': data['gotify_token']
            }
        )
        return redirect(url_for('front_index'))

    return render_template('add_user.html')


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
