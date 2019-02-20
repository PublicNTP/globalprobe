#!/usr/bin/python3

import boto3
import logging
import os
import sys
import pprint
from warrant.aws_srp import AWSSRP
import requests
import psycopg2


def _clearTestData(logger, dbConnection, dbCursor ):

    try:

        dbCursor.execute(
            "DELETE FROM monitored_servers WHERE dns_name LIKE '%.globalprobe.dev.publicntp.org';" )

        dbConnection.commit()

    except Exception as e:
        logger.error("Could not clear test data: {0}".format(e))
        sys.exit()


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

        results = dbCursor.fetchall()

        if len(results) == 0:
            logger.error("Did not find any rows for server \"{0}\" in backend SQL database".format(
                serverData['server_address']) )
            sys.exit()

        addressesFound = []

        for currRow in results:

            if currRow[2] != serverData['display_name']:
                logger.error("Invalid display name in results row {0} for server {1}".format(
                    pprint.pformat(currRow), serverData['server_address']) )
                sys.exit()

            if currRow[3] != serverData['display_description']:
                logger.error("Invalid display description in results row {0} for server {1}".format(
                    pprint.pformat(currRow), serverData['server_address']) )
                sys.exit()


            if currRow[4] != serverData['display_location']:
                logger.error("Invalid display location in results row {0} for server {1}".format(
                    pprint.pformat(currRow), serverData['server_address']) )
                sys.exit()

            if currRow[5] != serverData['notes']:
                logger.error("Invalid display notes in results row {0} for server {1}".format(
                    pprint.pformat(currRow), serverData['server_address']) )
                sys.exit()

            addressesFound.append( currRow[6] )

        
        # If sorted, double equals test should work
        addressesFound.sort()
        serverData['server_addresses'].sort()
        if addressesFound != serverData['server_addresses']:
            logger.error("Addresses found {0} does not match expected addresses {1}".format(
                pprint.pformat(addressesFound), pprint.pformat(serverData['server_address'])) )

            sys.exit()
        else:
            logger.info("Found all expected addresses: {0}".format(pprint.pformat(serverData['server_addresses'])))


        logger.info("Unit test passed for {0}".format(serverData['server_address']))

    except Exception as e:
        logger.error("Something went boom in validation. {0}".format(e))
        sys.exit()



def _getNewServerData():
    ownerUuid = '3665f15f-36d8-42d4-b531-aa9284126bfe'

    serversToAdd = [
        {
            'server_address'        : 'unittest2.globalprobe.dev.publicntp.org',
            'owner_id'              : ownerUuid,
            'display_name'          : 'Unit Test 2',
            'display_description'   : 'Do some testing',
            'display_location'      : 'Does not exist',
            'notes'                 : 'Notes for testing',

            'server_addresses'      : [
                                        '127.1.2.3',
                                        '127.2.3.4',
                                        '::1'
                                    ]
        },


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


def _addNewServers(logger, serversToAdd, dbCursor):

    try:
        logger.info("We have {0} servers to add".format(len(serversToAdd)) )
        for currServer in serversToAdd:
            _addServer(logger, currServer)
            _validateServerAddedCorrectly(logger, currServer, dbCursor)


    except Exception as e:
        logger.error("Something blowed up: {0}".format(e))
        sys.exit()


   

def main(logger):
    newServers = _getNewServerData()

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
                _clearTestData(logger, dbConnection, dbCursor)
                _addNewServers(logger, newServers, dbCursor )
                _clearTestData(logger, dbConnection, dbCursor)
    except Exception as e:
        logger.error("Boom: {0}".format(e))
        sys.exit()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Turn up level on other modules that spam
    logging.getLogger('boto3').setLevel(logging.WARN)
    logging.getLogger('urllib3').setLevel(logging.WARN)
    logging.getLogger('botocore').setLevel(logging.WARN)

    main(logger)
