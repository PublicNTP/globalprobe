import boto3
import logging
import os
import sys
import pprint
from warrant.aws_srp import AWSSRP


def _clearTestData():
    pass


def _validateServerAddedCorrectly(serverData):
    pass


def _getNewServerData():

    serversToAdd = [
        {
            'server_address'        : 'server1.unittest',
            'display_name'          : 'DisplayName for server1.unittest',
            'display_description'   : 'Description for server1.unittest',
            'display_location'      : 'Locaiton for server1.unittest',
            'notes'                 : 'Notes for server1.unittest'
        },
    ]

    return serversToAdd

def _getCognitoUserTokens(logger):

    userPoolId = 'us-east-2_QPz9qLkQL'
    appClientId = '3qkoupgav6gbvs4cbebphqbdlq'
    globalProbeUser         = os.environ['GLOBALPROBE_USER']
    globalProbePassword     = os.environ['GLOBALPROBE_PASSWORD']

    awsRegion = 'us-east-2'

    botoClient = boto3.client('cognito-idp', region_name=awsRegion )

    try:
        awsSrpClient = AWSSRP(
            username    = globalProbeUser,
            password    = globalProbePassword,
            pool_id     = userPoolId,
            client_id   = appClientId,
            client      = botoClient )

    except Exception as e:
        logger.error("Could not create AWSSRP client for user {0}, exception: {1}".format(
            globalProbeUser, e) )

        sys.exit()

    try:
        tokens = awsSrpClient.authenticate_user()
    except Exception as e:
        logger.error("Could not authenticate user {0}, exception: {1}".format(
            globalProbeUser, e) )
        sys.exit()

    print("Successful login as GloblProbe user \"{0}\"".format(globalProbeUser))

    #print( "Tokens:\n{0}".format(pprint.pformat(tokens)) )

    cognitoTokens = {
        'access'        : tokens['AuthenticationResult']['AccessToken'],
        'identity'      : tokens['AuthenticationResult']['IdToken'],
        'refresh'       : tokens['AuthenticationResult']['RefreshToken']
    }

    return cognitoTokens
     


def _cognitoLogout(logger, cognitoLogin):
    pass

def _addServer(logger, serverDetails):
    cognitoTokens = _getCognitoUserTokens(logger)


    _cognitoLogout(logger, cognitoTokens)


def _addNewServers(logger, serversToAdd):
    for currServer in serversToAdd:
        _addServer(logger, currServer)
        _validateServerAddedCorrectly(currServer)

   

def main(logger):
    newServers = _getNewServerData()

    _clearTestData()

    _addNewServers(logger, newServers)


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    main(logger)
