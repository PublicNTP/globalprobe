#!/usr/bin/python3

import boto3
import logging
import os
import sys
import pprint
from warrant.aws_srp import AWSSRP
import requests
import psycopg2
import json



def _attemptServerHistory(logger, newServers, dbConnection, dbCursor):

    serverHistoryEndpoint = "https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/server/history/last_n_secs/86400"

    cognitoTokens = _getCognitoUserTokens()
    authHeaders = {
        "Authorization": cognitoTokens['identity']
    }

    historyAttempt = requests.get( serverHistoryEndpoint, headers=authHeaders)

    if historyAttempt.status_code == 200:
        logger.info("API claims it got history for {0}".format(os.environ['GLOBALPROBE_USER']) )

        logger.info("Return value: {0}".format(json.dumps(historyAttempt.json())))


    else:
        logger.error("Could not get history for {0}".format(os.environ['GLOBALPROBE_USER']))

    _cognitoLogout(cognitoTokens)

    cognitoTokens = None

    for currServerName in newServers:
        currServer = newServers[currServerName]

        pass


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
        'unittest-history01.globalprobe.dev.publicntp.org': {
            'display_name'          : 'Unit Test List',
            'display_description'   : 'I think we are supposed to test',
            'display_location'      : 'Right, testing sounds good',
            'notes'                 : 'Kick that testing in the tail',
            'server_addresses'      : [
                '127.9.9.9',
                '127.9.8.7',
                '::1'
            ]
        },

        
        'unittest-history02.globalprobe.dev.publicntp.org': {
            'display_name'          : 'Second unit test server',
            'display_description'   : 'Some description would be good here',
            'display_location'      : 'I think the server exists in reality',
            'notes'                 : 'Notes are for the weak',
            'server_addresses'      : [
                '127.127.127.128',
                '127.128.129.130',
                '2406:da12:852:5800:1219:dc1e:dd35:8888'
            ]
        },
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

            dbCursor.execute(
                "INSERT INTO service_probes ( probe_site_id, server_address, time_request_sent, time_response_received, " +
                    "round_trip_time, estimated_utc_offset) " +
                "VALUES ( (SELECT MIN(probe_site_id) FROM probe_sites), (SELECT server_address_id FROM server_addresses WHERE address = %s), " +
                    "NOW() - interval '100 seconds', " +
                    "NOW() - interval '99 seconds', interval '1 second', interval '0.0004 seconds');",

                (currAddress,)
            )



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
                _attemptServerHistory(logger, newServers, dbConnection, dbCursor)
                #_clearTestData(logger, dbConnection, dbCursor)

                
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
