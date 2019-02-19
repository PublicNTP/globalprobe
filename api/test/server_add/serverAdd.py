import boto3
import logging
import os
import sys
import pprint
from warrant.aws_srp import AWSSRP
import requests
import psycopg2


def _clearTestData():
    pass


def _validateServerAddedCorrectly(logger, serverData, dbCursor):

    try:
        dbCursor.execute( 
            "SELECT owner_cognito_id, dns_name, display_name, display_description, display_location, notes, address " + 
            "FROM monitored_servers " +
            "LEFT OUTER JOIN server_addresses " + 
            "ON monitored_servers.server_id = server_addresses.server_id " +
            "WHERE monitored_servers.dns_name = %s;",

            (serverData['server_address'],)
        )

        results = dbCursor.fetchall()[0]

        if results[1] == serverData['server_address']:
            logger.info("Confirmed that server \"{0}\" is now in the backend SQL database".format(
                serverData['server_address']) )


        #logger.info("Results:\n{0}\n".format(pprint.pformat(results)))

    except Exception as e:
        logger.error("Something went boom in validation")
        sys.exit()



def _getNewServerData():

    serversToAdd = [
        {
            'server_address'        : 'server1.unittest',
            'display_name'          : 'DisplayName for server1.unittest',
            'display_description'   : 'Description for server1.unittest',
            'display_location'      : 'Locaiton for server1.unittest',
            'notes'                 : 'Notes for server1.unittest'
        }
    ]

    return serversToAdd

def _getCognitoUserTokens():

    userPoolId = 'us-east-2_QPz9qLkQL'
    appClientId = '3qkoupgav6gbvs4cbebphqbdlq'
    globalProbeUser         = os.environ['GLOBALPROBE_USER']
    globalProbePassword     = os.environ['GLOBALPROBE_PASSWORD']

    awsRegion = 'us-east-2'

    logger = logging.getLogger(__name__)

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

    logger.info("Successful login as GlobalProbe user \"{0}\"".format(globalProbeUser))

    #print( "Tokens:\n{0}".format(pprint.pformat(tokens)) )

    cognitoTokens = {
        'access'        : tokens['AuthenticationResult']['AccessToken'],
        'identity'      : tokens['AuthenticationResult']['IdToken'],
        'refresh'       : tokens['AuthenticationResult']['RefreshToken']
    }

    return cognitoTokens
     


def _cognitoLogout(cognitoLogin):
    pass

def _addServer(logger, serverDetails):
    cognitoTokens = _getCognitoUserTokens()

    # Add the server via the API
    addServerRestEndpoint = "https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/server/add"

    addServerBody = {
        "new_server": serverDetails 
    }

    # We have to prove we're a valid user to interact with the API
    postHeaders = {
        "Authorization": cognitoTokens['identity']
    }

    logger.info("Using REST API endpoint to attempt adding server \"{0}\"".format(serverDetails['server_address']) )


    addAttempt = requests.post( addServerRestEndpoint, json=addServerBody, headers=postHeaders )

    if addAttempt.status_code == 200:
        logger.info("API claims it added server \"{0}\"".format(serverDetails['server_address']) )
    else:
        logger.warn( "API response status code: {0}".format(addAttempt.status_code) )
    

    _cognitoLogout(cognitoTokens)


def _addNewServers(logger, serversToAdd):

    dbDetails = {
        'db_name': os.environ['GLOBALPROBE_DBNAME'],
        'db_user': os.environ['GLOBALPROBE_DBUSER'],
        'db_host': os.environ['GLOBALPROBE_DBHOST'],
        'db_passwd': os.environ['GLOBALPROBE_DBPASSWD']
    }

    try:
        with psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
                dbDetails['db_name'],
                dbDetails['db_user'],
                dbDetails['db_host'],
                dbDetails['db_passwd']
            )
        ) as dbConnection:
            with dbConnection.cursor() as dbCursor:
                logger.info("We have {0} servers to add".format(len(serversToAdd)) )
                for currServer in serversToAdd:
                    _addServer(logger, currServer)
                    _validateServerAddedCorrectly(logger, currServer, dbCursor)


    except Exception as e:
        logger.error("Something blowed up: {0}".format(e))
        sys.exit()


   

def main(logger):
    newServers = _getNewServerData()

    _clearTestData()

    _addNewServers(logger, newServers)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Turn up level on other modules that spam
    logging.getLogger('boto3').setLevel(logging.WARN)
    logging.getLogger('urllib3').setLevel(logging.WARN)
    logging.getLogger('botocore').setLevel(logging.WARN)

    main(logger)
