import json
import socket
import logging
import pprint
import os
import psycopg2


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


def _addDatabaseEntry(logger, serverFqdn, serverAddresses):
   
    dbDetails = {
        'db_host'       : os.environ['db_host'],
        'db_user'       : os.environ['db_user'],
        'db_passwd'     : os.environ['db_passwd'],
        'db_name'       : 'globalprobe'
    }

    logger.debug("DB info:\n\tHost: {0}\n\tUser: {1}\n\tPassword: {2}\n\tUser: {3}".format(
        dbDetails['db_host'],
        dbDetails['db_user'],
        dbDetails['db_passwd'],
        dbDetails['db_name']) 
    )

    # Need owner's UUID -- Cognito, how do we get this?
    ownerUuid = '3665f15f-36d8-42d4-b531-aa9284126bfe'
   

    try:
        with psycopg2.connect("dbname='{0}' user='{1}' host='{2}' password='{3}'".format(
                dbDetails['db_name'],
                dbDetails['db_user'],
                dbDetails['db_host'],
                dbDetails['db_passwd']
            )
        ) as dbConnection:
            with dbConnection.cursor() as dbCursor:

                # Add server
                dbCursor.execute( "INSERT INTO monitored_servers (owner_cognito_id, dns_name) " + 
                    "VALUES (%s, %s) " +
                    "RETURNING server_id;",
                    (ownerUuid, serverFqdn) )

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
    except:
        logger.error("Exception of unknown type thrown during DB add")


def _processServerAdd(logger, event):
    bodyJson = json.loads(event['body'])

    # Resolve all addresses for our new server
    newServerFQDN = bodyJson['new_server']['server_address']
    newServerIpAddresses = _resolveDnsName(logger, newServerFQDN)

    # Add the new server into our database of servers being monitored
    _addDatabaseEntry(logger, newServerFQDN, newServerIpAddresses)

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

def _createLogger():

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    return logger


def globalprobe_api(event, context):

    logger = _createLogger() 
    
    if event['path'] == '/v1/server/add':
        response = _processServerAdd(logger, event)

    else:
        logger.warn("Invalid path: {0}".format(event['path']) )

        response = {
            "statusCode": 200,
            "body": "Unknown operation"
        }

    return response
