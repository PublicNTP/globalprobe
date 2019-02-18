import boto3

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

def _getIdentityToken():
    pass


def _logoutOfApi(identityToken):
    pass

def _addServer(serverDetails):
    identityToken = _getIdentityToken()

    _logoutOfApi(identityToken)


def _addNewServers(serversToAdd):
    for currServer in serversToAdd:
        _addServer(currServer)
        _validateServerAddedCorrectly(currServer)

   

def main():
    newServers = _getNewServerData()

    _clearTestData()

    _addNewServers(newServers)


if __name__ == "__main__":
    main()
