import os, json, requests
import sys, time
import urllib

from flask import Flask, request, redirect, url_for, flash

from flask import jsonify

from flask_sqlalchemy import SQLAlchemy

from flask_heroku import Heroku

app = Flask(__name__)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://tmtfkfkrsfslju:a309076a45cb78b177bb9368b275cfdedf16422d2d01fb8ffc1fee1e7bee604d@ec2-23-23-225-12.compute-1.amazonaws.com:5432/d1g76agkrjaf2o'
heroku = Heroku(app)
db = SQLAlchemy(app)

# Create our database model


class User_id(db.Model):
    __tablename__ = 'user_id'

    name = db.Column(db.String(30), primary_key=True)
    message_id = db.Column(db.String(100), nullable=False)
    def __init__(self, name, message_id):
        self.name = name
        self.message_id = message_id
    def __repr__(self):
        return '<name {}>'.format(self.name)

@app.route("/")
def index():
    return "Hello World"

@app.route('/webhook', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "ok", 200

@app.route('/webhook', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    def generate():
        base_url = "https://graph.facebook.com/v2.8/"
        access_token = os.environ["PAGE_ACCESS_TOKEN"]
        data = request.get_json()
        try:
            if data["object"] == "page":
                if data["entry"][0]["messaging"]:
                    sender_id = data["entry"][0]["messaging"][0]["sender"]["id"]
                    # the facebook ID of the person sending you the message 

                    final_url = base_url+sender_id+"?"+"access_token="+access_token
                    print final_url

                    resp = requests.get(final_url)
                    user_data = resp.json()
                    sender_fname = user_data["first_name"]
                    sender_fname_stripped = sender_fname.split()[0]
                    sender_lname = user_data["last_name"]
                    sender_name = sender_fname+" "+sender_lname

                    # print sender_name
                    u_count = User_id.query.filter_by(name = sender_name).first()
                    log(u_count)
                    if u_count is None:
                        
                        new_time = int(time.time())
                        db_add = User_id(name=sender_name, message_id=sender_id)
                        db.session.add(db_add)
                        db.session.commit()

                        message_data = "Hello! Thanks for liking my FB page, please subscribe to my youtube channel as well if you haven't already https://www.youtube.com/comfuzio . It means a great deal to me. Thank you!" 
                        send_message(sender_id, message_data)

                    else:
			message_data = "Thanks for messaging me, I will reply to you the sooner I can! <3"
			send_message(sender_id, message_data)
        except:
            pass
    return "ok", 200, generate()

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })

    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200


def send_state(recipient_id):

    log("sending state to {recipient}: ".format(recipient=recipient_id))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action":"typing_on"

    })
    r = requests.post("https://graph.facebook.com/v2.8/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    return "ok", 200

def send_status(recipient_id):
    return "ok", 200

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

if __name__ == '__main__':
    app.run(debug=True)
