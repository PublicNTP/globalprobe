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



def _attemptAlertAdds(logger, dbConnection, dbCursor):

    addAlertsEndpoint = "https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/alert/add"

    cognitoTokens = _getCognitoUserTokens()
    authHeaders = {
        "Authorization": cognitoTokens['identity']
    }

    newAlerts = [
        {
            "server_hostname": "stratum2-01.ord01.publicntp.org",
            "alert_type": "duration_down",
            "down_duration_trigger_minutes": 10,
            "alert_method": "email",
            "email_address": "outage_alert@publicntp.org",
            "alert_holdoff_minutes": 60
        },

        {
            "server_hostname": "stratum2-01.icn01.publicntp.org",
            "alert_type": "percentage_drop_over_duration",
            "percentage_drop_trigger": 10,
            "duration_trigger_minutes": 30,
            "alert_method": "email",
            "email_address": "outage_alert@publicntp.org",
            "alert_holdoff_minutes": 60
        }
    ]

    for i in range(len(newAlerts)):

        addAttempt = requests.post( addAlertsEndpoint, headers=authHeaders, json={ "alert": newAlerts[i] } )

        if addAttempt.status_code == 200:
            logger.info("API claims it added alert" )

            returnedBody = addAttempt.json()
            alertId = returnedBody['generated_alert_id']


            logger.info("New alert ID: {0}".format(alertId))

        else:
            logger.debug(json.dumps(addAttempt))
            logger.error("Could not add alert")


    logger.info("Test complete")


def _clearTestData(logger, dbConnection, dbCursor ):

    logger.info("Clearing test data")

    try:

        dbCursor.execute(
            "DELETE FROM monitored_servers " + \
            "WHERE monitored_servers.dns_name LIKE '%.globalprobe.dev.publicntp.org';" )

        dbConnection.commit()

    except Exception as e:
        logger.error("Could not clear test data: {0}".format(e))
        sys.exit()



def _getTestData():
    hostsToAdd = {
        'unittest-alert-list-01.globalprobe.dev.publicntp.org': {
            'display_name'          : 'Unit Test',
            'display_description'   : 'I think we are supposed to test',
            'display_location'      : 'Right, testing sounds good',
            'notes'                 : 'Kick that testing in the tail',
            'server_addresses'      : [
                '127.4.49.198',
                '127.127.198.49'
            ]
        },

        'unittest-alert-list-02.globalprobe.dev.publicntp.org': {
            'display_name'          : 'Unit Test',
            'display_description'   : 'test and then test some more',
            'display_location'      : 'somewhere they test stuff',
            'notes'                 : 'booya',
            'server_addresses'      : [
                '127.126.125.124'
            ]
        }

    }

    alertsToAdd = {
        'unittest-alert-list-01.globalprobe.dev.publicntp.org': [
            {
                'alert_method': 'email',
                'email_address': 'terry.ott@publicntp.org',
                'alert_type': 'outage_duration_minutes',
                'alert_value': 10,
                'notification_holdoff_minutes': 60 
            }
        ],

        'unittest-alert-list-02.globalprobe.dev.publicntp.org': [
            {
                'alert_method': 'email',
                'email_address': 'terry.ott@publicntp.org',
                'alert_type': 'percentage_drop',
                'alert_drop_percentage': 5,
                'alert_drop_percentage_duration_window_minutes': 60,
                'notification_holdoff_minutes': 60
            }
        ]
    }

    return { 'servers': hostsToAdd, 'alerts': alertsToAdd }


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


def _addAlertsToSql(logger, alertsToAdd, dbConnection, dbCursor):

    try:
        logger.info("We have {0} alerts to add".format(len(alertsToAdd)) )
        for currHost in alertsToAdd:
            for currAlertIndex in range(len(alertsToAdd[currHost])):
                currAlert = alertsToAdd[currHost][currAlertIndex]

                logger.info( "Adding alert:\n{0}".format(pprint.pformat(currAlert)) )

                if currAlert['alert_type'] == 'outage_duration_minutes':
                    _addDurationAlert(currAlert, dbConnection, dbCursor)


                elif currAlert['alert_type'] == 'percentage_drop':
                    _addPercentageDropAlert(currAlert, dbConnection, dbCursor)


    except Exception as e:
        logger.error("Something blowed up when adding alerts: {0}".format(e))
        sys.exit()


   

def main(logger):
    #testData = _getTestData()

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
                #_clearTestData(logger, dbConnection, dbCursor)
                #_addServersToSql(logger, testData['servers'], dbConnection, dbCursor )
                #_addAlertsToSql(logger, testData['alerts'], dbConnection, dbCursor )
                _attemptAlertAdds(logger, dbConnection, dbCursor)
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
