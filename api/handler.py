import json
import socket
import logging
import pprint
import os
import psycopg2
import re


def _getCognitoUsername(event):
    requestContext      = event['requestContext']
    authorizer          = requestContext['authorizer']
    claims              = authorizer['claims']

    return claims['cognito:username']


def _connectToDB( ):
    dbDetails = {
        'db_host'       : os.environ['db_host'],
        'db_user'       : os.environ['db_user'],
        'db_passwd'     : os.environ['db_passwd'],
        'db_name'       : 'globalprobe'
    }

    return psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format( 
        dbDetails['db_name'],
        dbDetails['db_user'],
        dbDetails['db_host'],
        dbDetails['db_passwd'])
    )



def _resolveDnsName(logger, newServerFqdn):

    resolvedAddresses = {
        'ipv4': [],
        'ipv6': []
    }

    try:
        # Very weird, but to get both IPv4 and IPv6 addresses for a DNS 
        #   name, you need to pretend like you're opening a connection
        #   to a port on that box, and see what address options you 
        #   get back.  ?!??!

        ntpDetails = {
            'port'          : 123,                  # NTP is hosted on port udp/123
            'family'        : socket.AF_UNSPEC,     # 0, or "Unspecified"
            'socket_type'   : 0,                    # Appears to be unspecified as well
            'protocol'      : socket.IPPROTO_UDP    # NTP is is a UDP protocol
        }

        logger.debug("Resolving DNS hostname {0}".format(newServerFqdn) )

        addressList = socket.getaddrinfo(
            newServerFqdn,          
            ntpDetails['port'],
            ntpDetails['family'],
            ntpDetails['socket_type'],
            ntpDetails['protocol']
        )

        for (currFamily, currSocketType, currProto, currCanonName, socketAddress) in addressList:
            # IPv4
            if currFamily == socket.AF_INET:
                logger.debug("Found IPv4 address: {0}".format(socketAddress[0]))
                addressList =  resolvedAddresses['ipv4']

                
            elif currFamily == socket.AF_INET6:
                logger.debug("Found IPv6 address: {0}".format(socketAddress[0]))
                addressList = resolvedAddresses['ipv6'] 

            else:
                logger.debug("Unsupported address type")
                next

            addressList.append(socketAddress[0])


    except socket.gaierror as e:
        logger.warn("DNS lookup threw exception: {0}".format(pprint.pformat(e)))

    return resolvedAddresses


def _addDatabaseEntry(logger, ownerUuid, serverFqdn, serverName, serverDescription, serverLocation, 
        serverNotes, serverAddresses):
   
    try:
        with _connectToDB() as dbConnection:
            with dbConnection.cursor() as dbCursor:

                # Add server
                dbCursor.execute( 
                    "INSERT INTO monitored_servers " +
                        "(owner_cognito_id, dns_name, display_name, display_description, display_location, notes) " + 
                    "VALUES (%s, %s, %s, %s, %s, %s) " +
                    "RETURNING server_id;",
                    (ownerUuid, serverFqdn, serverName, serverDescription, serverLocation, serverNotes) )

                # Get the new server ID back out
                newServerId = dbCursor.fetchone()[0]

                # add server addresses
                for currAddress in serverAddresses['ipv4']:
                    dbCursor.execute( "INSERT INTO server_addresses (server_id, address) " +
                        " VALUES (%s, %s);",
                        ( newServerId, currAddress ) )

                for currAddress in serverAddresses['ipv6']:
                    dbCursor.execute( "INSERT INTO server_addresses (server_id, address) " +
                        " VALUES (%s, %s);",
                        ( newServerId, currAddress ) )
                
                # We're in a transaction, so commit it before we close and lose it
                dbConnection.commit()
    except Exception as e:
        logger.error("Exception of unknown type thrown during DB add: {0}".format(e))


def _processServerAdd(logger, event):
    logger.info("Body: {0}".format(event['body']))
    bodyJson = json.loads(event['body'])

    newServerFQDN = list(bodyJson.keys())[0]
    ownerCognitoId = _getCognitoUsername(event)

    # Resolve all addresses for our new server
    newServerIpAddresses = _resolveDnsName(logger, newServerFQDN)

    newServerName = bodyJson[newServerFQDN]['display_name']
    newServerDescription = bodyJson[newServerFQDN]['display_description']
    newServerLocation = bodyJson[newServerFQDN]['display_location']
    newServerNotes = bodyJson[newServerFQDN]['notes']

    # Add the new server into our database of servers being monitored
    _addDatabaseEntry(logger, ownerCognitoId, newServerFQDN, newServerName,
        newServerDescription, newServerLocation, newServerNotes, newServerIpAddresses)

    returnBody = "Processed server add request\n\tNew server FQDN: {0}\n".format(newServerFQDN) + \
        "\nResolved addresses:\n\t\tIPv4: {0}\n\t\tIPv6: {1}\n".format(
            pprint.pformat(newServerIpAddresses['ipv4']),
            pprint.pformat(newServerIpAddresses['ipv6']) )
    

    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        "body": returnBody
    }


def _processServerDelete(logger, serverToDelete):
    logger.info("Trying to delete server {0}".format(
        pprint.pformat(serverToDelete)) )

    try:
        with _connectToDB() as dbConnection:
            with dbConnection.cursor() as dbCursor:
                # Add server
                dbCursor.execute( "DELETE FROM monitored_servers WHERE dns_name = %s;",
                    (serverToDelete, ) )

                dbConnection.commit()

    except Exception as e:
        logger.error("Exception thrown in delete: {0}".format(e) )
        
          

    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        "body": "Deleted server \"{0}\"".format(serverToDelete)
    }


def _processServerList(logger, event):
    cognitoUsername     = _getCognitoUsername(event)
    serverList = {}

    try:
        with _connectToDB() as dbConnection:
            with dbConnection.cursor() as dbCursor:
                # List all servers for the given user ID

                dbCursor.execute( 
                    "SELECT dns_name, display_name, display_description, display_location, " +
                            "notes, address " +
                    "FROM monitored_servers " +
                    "JOIN server_addresses " + 
                    "ON monitored_servers.server_id = server_addresses.server_id " +
                    "WHERE owner_cognito_id = %s " +
                    "ORDER BY dns_name, address;",

                    (cognitoUsername, ) )

                listResults = dbCursor.fetchall()

                for currResult in listResults:
                    if currResult[0] not in serverList:
                        serverList[ currResult[0] ] = {
                            'display_name'          : currResult[1],
                            'display_description'   : currResult[2],
                            'display_location'      : currResult[3],
                            'notes'                 : currResult[4],
                            'server_addresses'      : []
                        }

                    serverList[ currResult[0] ][ 'server_addresses' ].append(currResult[5] )

    except Exception as e:
        logger.error("Exception thrown in list: {0}".format(e) )

    return {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        "body": json.dumps( { 'servers': serverList } )
    }


def _processServerHistory(logger, event):

    result = re.match('\/v1/server\/history\/last_n_secs\/(\d+)\/ip_address\/(.+)/?', event['path'])

    cognitoUsername     = _getCognitoUsername(event)

    if result is not None:
        timeWindowSeconds = result.group(1)
        ipAddress = result.group(2)

        response = _getServerHistory(logger, timeWindowSeconds, cognitoUsername, ip_address=ipAddress)
    else:
        response = {
            "statusCode": 502,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            "body": json.dumps( {'invalid_request': event['path']} )
        }

    return response


def _getServerHistory(logger, timeWindowSeconds, cognitoUsername, ip_address=None, dns_fqdn=None):
    
    logger.info("Inside pull server history. Time window = {0}, ip_address = {1}, dns_fqdn={2}".format(
        timeWindowSeconds, ip_address, dns_fqdn) )

    if ip_address is not None:
        whereClause = " WHERE server_addresses.address = ? "
    elif dns_fqdn is not None:
        whereClause = " WHERE monitored_servers.dns_name = ? "
    else:
        whereClause = ""

    probeHistory = {}

    try:
        with _connectToDB() as dbConnection:
            with dbConnection.cursor() as dbCursor:
                
                dbCursor.execute(
                    "SELECT dns_name, address, time_request_sent, time_response_received, " +
                        "round_trip_time, estimated_utc_offset, site_location_id " +
                    "FROM monitored_servers " +
                    "JOIN server_addresses " +
                    "ON monitored_servers.server_id = server_addresses.server_id " +
                    "JOIN service_probes " +
                    "ON server_addresses.server_address_id = service_probes.server_address " +
                    "JOIN probe_sites " +
                    "ON service_probes.probe_site_id = probe_sites.probe_site_id " +
                    "WHERE owner_cognito_id = %s " +
                    "AND NOW() - time_request_sent <= interval '%s seconds' " +
                    "AND address = %s " 
                    "ORDER BY dns_name, address, time_request_sent, probe_sites.probe_site_id;",

                    (cognitoUsername, int(timeWindowSeconds), ip_address) )

                historyResults = dbCursor.fetchall()

    except Exception as e:
        logger.error("Exception thrown in server history: {0}".format(e) )

    #logger.info("What the fuck in results? How did it get so fucked?\n{0}".format(pprint.pformat(historyResults)))

    for currRow in historyResults:
        logger.info("Curr row:\n{0}".format(pprint.pformat(currRow)))

        dnsName             = currRow[0]
        address             = currRow[1]
        timeSent            = currRow[2]
        timeRecv            = currRow[3]
        rtt                 = currRow[4]
        estimatedOffset     = currRow[5]
        probeSite           = currRow[6]


        if dnsName not in probeHistory:
            probeHistory[dnsName] = {}

        if address not in probeHistory[dnsName]:
            probeHistory[dnsName][address] = []


        probeHistory[dnsName][address].append( 
            {
                'probe_site'                    : probeSite,
                'request_sent'                  : timeSent.isoformat(),
                'response_received'             : timeRecv.isoformat(),
                'round_trip_time_secs'          : rtt.total_seconds(),
                'local_remote_utc_offset_secs'  : estimatedOffset.total_seconds()
            }
        )

        #logger.info("Added probe data:\n{0}".format(pprint.pformat(probeHistory)))

    

    historyResponse = {
        "statusCode": 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        "body": json.dumps(probeHistory)
    }

    return historyResponse


def _createLogger():

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    return logger


def globalprobe_api(event, context):

    logger = _createLogger() 
    
    if event['httpMethod'] == 'POST' and event['path'] == '/v1/server':
        logger.info("Entry to add")
        response = _processServerAdd(logger, event)

    # TODO: refactor this to do the RE in the function
    elif event['httpMethod'] == 'DELETE':
        logger.info("Entry to delete")
        result = re.match('\/v1/server\/(.+)', event['path'])

        if result is not None:
            serverToDelete = result.group(1)
            response = _processServerDelete(logger, serverToDelete)
        else:
            response = {
                "statusCode": 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                "body": "Could not delete server {0}".format(event['path'])

            }

    elif event['httpMethod'] == 'GET' and event['path'] == '/v1/server/list':
        logger.info("Entry to list")
        response = _processServerList(logger, event)


    elif event['httpMethod'] == 'GET' and event['path'].startswith('/v1/server/history'):
        logger.info("Checking server history")
        response = _processServerHistory(logger, event)
    

    else:
        logger.warn("Invalid path: {0}".format(event['path']) )
        logger.warn( "Event: {0}".format(pprint.pformat(event)) )

        response = {
            "statusCode": 200,
            "body": "Unknown operation"
        }

    return response
