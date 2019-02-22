#!/usr/bin/python3

import boto3
import logging
import os
import sys
import pprint
from warrant.aws_srp import AWSSRP
import requests
import psycopg2



def _attemptServerList(logger, newServers, dbConnection, dbCursor):

    listServersEndpoint = "https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/server/list"

    for currServer in newServers:
        cognitoTokens = _getCognitoUserTokens()
        authHeaders = {
            "Authorization": cognitoTokens['identity']
        }

        listAttempt = requests.get( listServersEndpoint, headers=authHeaders)

        if listAttempt.status_code == 200:
            logger.info("API claims it listed servers" )

            returnedBody = listAttempt.json()
            apiServers = returnedBody['servers']

            for checkServerName in newServers:
                checkServer = newServers[checkServerName]
                checkServer['server_addresses'].sort()
                if checkServerName not in apiServers:
                    logger.error("Did not find test server {0}".format(checkServerName))
                    sys.exit()

                currRecord = apiServers[checkServerName]

                if currRecord != checkServer:
                    logger.error("Fields did not match for {0}".format(currServer))
                    logger.error("currRecord = {0}".format(pprint.pformat(currRecord)))
                    logger.error("check server = {0}".format(pprint.pformat(checkServer)))
                    sys.exit()


            logger.info("Test passed!")

        else:
            logger.error("Could not list servers")




        _cognitoLogout(cognitoTokens)





def _clearTestData(logger, dbConnection, dbCursor ):

    try:

        dbCursor.execute(
            "DELETE FROM monitored_servers WHERE dns_name LIKE '%.globalprobe.dev.publicntp.org';" )

        dbConnection.commit()

    except Exception as e:
        logger.error("Could not clear test data: {0}".format(e))
        sys.exit()



def _getNewServerData():
    serversToAdd = {
        'unittest-list.globalprobe.dev.publicntp.org': {
            'display_name'          : 'Unit Test List',
            'display_description'   : 'I think we are supposed to test',
            'display_location'      : 'Right, testing sounds good',
            'notes'                 : 'Kick that testing in the tail',
            'server_addresses'      : [
                '127.9.9.9',
                '127.9.8.7',
                '::1'
            ]
        }
    }

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

def _addServerToSql(logger, serverName, serverDetails, dbConnection, dbCursor):
    ownerUuid = '3665f15f-36d8-42d4-b531-aa9284126bfe'

    try:
        dbCursor.execute(
            "INSERT INTO monitored_servers (owner_cognito_id, dns_name, display_name, display_description, display_location, notes)" +
            "VALUES (%s, %s, %s, %s, %s, %s) " +
            "RETURNING server_id;",

            (ownerUuid, serverName,
             serverDetails['display_name'], serverDetails['display_description'], 
             serverDetails['display_location'], serverDetails['notes']) )

        serverId = dbCursor.fetchone()[0]

        for currAddress in serverDetails['server_addresses']:
            dbCursor.execute(
                "INSERT INTO server_addresses (server_id, address) " +
                "VALUES (%s, %s);",

                (serverId, currAddress) )

        dbConnection.commit()

        #logger.info("Added {0}".format(serverDetails['server_address']))

    except Exception as e:
        logger.error("Could not add server we're going to list: {0}".format(e))
        sys.exit()



def _addServersToSql(logger, serversToAdd, dbConnection, dbCursor):

    try:
        logger.info("We have {0} servers to add".format(len(serversToAdd)) )
        for currServerName in serversToAdd:
            currServer = serversToAdd[currServerName]
            _addServerToSql(logger, currServerName, currServer, dbConnection, dbCursor)


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
                _addServersToSql(logger, newServers, dbConnection, dbCursor )
                _attemptServerList(logger, newServers, dbConnection, dbCursor)
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
