import json
import socket
import logging
import pprint


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



def _processServerAdd(logger, event):
    bodyJson = json.loads(event['body'])

    newServerFQDN = bodyJson['new_server']['server_address']

    newServerIpAddresses = _resolveDnsName(logger, newServerFQDN)

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
        A:w

        response = {
            "statusCode": 200,
            "body": "Unknown operation"
        }

    return response
