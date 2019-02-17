import json


def _processServerAdd(event):
    bodyJson = json.loads(event['body'])

    serverAddress = bodyJson['new_server']['server_address']

    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        "body": "Server add request\nServer address: {1}".format(serverAddress)
    }


def globalprobe_api(event, context):
    
    if event['path'] == '/v1/server/add':
        response = _processServerAdd(event)

    else:
        response = {
            "statusCode": 200,
            "body": "Unknown operation"
        }

    return response
