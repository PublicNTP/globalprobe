import json


def _processServerAdd(event):

    return {
        "statusCode": 200,
        "body": "Server add successful"
    }


def globalprobe_api(event, context):
    
    if event['path'] == '/v1/server/add':
        response = _processServerAdd(event)

    else:
        response = {
            "statusCode": 200,
            "body": "Unknown operation"
        }

    """
    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }
    """

    return response
