from jsonschema import validate
import praw
from flask import Flask, request
import json
import os
from flask_cors import CORS, cross_origin
from celery import Celery, group

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
redirect_uri = os.environ['REDIRECT_URI']

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
CORS(app, resources={r'/': {"origins": "benawad"}})

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


######### CELERY ###########
redis_url = os.environ['REDIS_URL']
celery = Celery(app.import_name, broker=redis_url)


@celery.task(serializer='pickle')
def _message(user, message, subject, reddit):
    ruser = reddit.redditor(user)
    try:
        ruser.message(subject, message)
    except:
        # future todo: message user that this message failed
        pass


def message_user(reddit, message, subject, users):
    g = group(_message.s(u, message, subject, reddit) for u in users)
    g.apply_async()


######### END CELERY ###########

 
def forbidden():
    print('forbidden')
    return json.dumps({"error": "forbidden"})


@app.route('/', methods=['OPTIONS', 'POST'])
@cross_origin(origin='benawad')
def handler():
    if request.method == 'POST':
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
            message_user(reddit, payload['message'], payload['subject'], payload['users'])
        return json.dumps([])
    else:
        return 'hi'


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
