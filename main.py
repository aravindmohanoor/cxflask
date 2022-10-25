import json
import logging
import os

import flask
import requests
from dotenv import load_dotenv
from flask import request
from google.auth.transport import requests as google_requests
from google.oauth2 import service_account

load_dotenv()

app = flask.Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':

        req = request.get_json(silent=True, force=True)
        try:
            if 'message' in req and 'text' in req.get('message'):
                response_json = {
                    "action": "reply",
                    "replies": [
                        "Sorry, there was some problem. Please try again later"
                    ]
                }
                json_str = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                json_data = json.loads(json_str)
                json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')
                CREDENTIAL_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
                credentials = service_account.Credentials.from_service_account_info(
                    json_data, scopes=CREDENTIAL_SCOPES)
                credentials.refresh(google_requests.Request())
                bearer_token = credentials.token

                usermsg = req.get('message').get('text')
                session_id = req.get('visitor').get('active_conversation_id')
                project_id = os.getenv('PROJECT_ID')
                location_id = os.getenv('LOCATION_ID')
                agent_id = os.getenv('AGENT_ID')
                url = f'https://dialogflow.googleapis.com/v3/projects/{project_id}/locations/' \
                      f'{location_id}/agents/{agent_id}/environments/-/sessions/{session_id}:detectIntent'
                headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Authorization': 'Bearer ' + bearer_token
                }
                payloadjson = {
                    "queryInput": {
                        "languageCode": "en",
                        "text": {
                            "text": usermsg,
                        }
                    },
                    "queryParams": {
                        "timeZone": "Asia/Calcutta"
                    }
                }
                payload = json.dumps(payloadjson)
                response = requests.request("POST", url, headers=headers, data=payload)
                result = json.loads(response.text)
                response_msgs = result['queryResult']['responseMessages']

                for response_msg in response_msgs:
                    if 'payload' in response_msg and 'platform' in response_msg.get('payload'):
                        if response_msg.get('payload').get('platform') == 'ZOHOSALESIQ':
                            response_json = response_msg.get('payload')
                    if 'text' in response_msg:
                        response_json['replies'] = response_msg['text']['text']
                return response_json

        except Exception as e:
            logging.exception("Response Error")

        return 'Post request'
    else:
        return 'Get request'


if __name__ == '__main__':
    app.run()
