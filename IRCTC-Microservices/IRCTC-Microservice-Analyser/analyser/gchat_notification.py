# Import required modules.

import os
import json
import dotenv
import httplib2
from mongo_connection import *

gchat_url = f"https://chat.googleapis.com/v1/spaces/AAAAtAX0JaE/messages?key={settings.GCHAT_KEY}&token={settings.GCHAT_TOKEN}"

def notify_gchat(message : str):
    '''
       Send message received to the google chat space.

       :param: message
       :ptype: str
    '''

    # Get the message that is to be send.
    send_message = {
        'text' : str(message)
    }
    
    # Set the format for the message.
    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}
     
    # Create the instance for the request.
    http_obj = httplib2.Http()
    
    # Send the message and the respose.
    response = http_obj.request(
        uri=gchat_url,
        method='POST',
        headers=message_headers,
        body=json.dumps(send_message),
    )

    try:
        print("***notification sent to gchat***")

    except Exception as e:

        print(e.msg())

