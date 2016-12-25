from jsonschema import validate
import multiprocessing as mp
import praw
from itertools import repeat
from flask import Flask, request
import json
import os

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
redirect_uri = os.environ['REDIRECT_URI']

app = Flask(__name__)

schema = {
    "type": "object",
    "properties": {
        "key": {
            "type": "string"
        },
        "code": {
            "type": "string"
        },
        "users": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "subject": {
            "type": "string"
        },
        "message": {
            "type": "string"
        }
    },
    "required": [
        "key",
        "code",
        "users",
        "subject",
        "message"
    ]
}


def forbidden():
    print('forbidden')
    return json.dumps({"error": "forbidden"})


def _message(user, message, subject, reddit):
    ruser = reddit.redditor(user)
    try:
        ruser.message(subject, message)
        success = True
    except:
        success = False
    return [user, success]


def message_user(reddit, message, subject, users):
    pool = mp.Pool(mp.cpu_count())
    return pool.starmap(_message,
            zip(users[:10], repeat(message),
            repeat(subject),
            repeat(reddit)))


@app.route('/', methods=['OPTIONS', 'POST'])
def handler():
    if request.method == 'POST':
        print(request.headers)
        try:
            payload = request.get_json()
            validate(payload, schema)
        except:
            return forbidden()
        if payload['key'] != 'yummy ramen':
            return forbidden()
        else:
            reddit = praw.Reddit(client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    user_agent="flask server")
            try:
                reddit.auth.authorize(payload['code'])
            except:
                return json.dumps({"authorization": "invalid"})
            successes = message_user(reddit, payload['message'], payload['subject'], payload['users'])
        return json.dumps(successes)
    else:
        return 'hi'


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
