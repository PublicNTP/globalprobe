
function attemptLogin()
{
    console.log("Attempting login");
    
    var submittedEmail = document.getElementById("input_email_address").value;
    var submittedPassword = document.getElementById("input_password").value;

    console.log("Checking username = \"" + submittedEmail + 
        "\", password = \"" + submittedPassword + "\"");


    var authenticationData = {
        Username : submittedEmail,
        Password : submittedPassword
    };

    var authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);

    var poolData = {
        UserPoolId  : 'us-east-2_QPz9qLkQL',
        ClientId    : '3qkoupgav6gbvs4cbebphqbdlq'
    };

    var userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

    var userData = {
        Username    : submittedEmail,
        Pool        : userPool
    };

    var cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    console.log("Ready to try to authenticate");

    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: function (result) {
            var accessToken = result.getAccessToken().getJwtToken();

            //POTENTIAL: Region needs to be set if not already set previously elsewhere.
            AWS.config.region = 'us-east-2';

            AWS.config.credentials = new AWS.CognitoIdentityCredentials({
                IdentityPoolId : 'us-east-2:8032efd3-ec81-452e-9e38-5120ec0d50b1',
                Logins : {
                    // Change the key below according to the specific region your user pool is in.
                    'cognito-idp.us-east-2.amazonaws.com/us-east-2:8032efd3-ec81-452e-9e38-5120ec0d50b1' : 
                        result.getIdToken().getJwtToken()
                }
            });

            //refreshes credentials using AWS.CognitoIdentity.getCredentialsForIdentity()
            AWS.config.credentials.refresh((error) => {
                if (error) {
                     console.error(error);
                } else {
                     // Instantiate aws sdk service objects now that the credentials have been updated.
                     // example: var s3 = new AWS.S3();
                     console.log('Successfully logged!');
                }
            });
        },

        onFailure: function(err) {
            alert(err.message || JSON.stringify(err));
        },

        newPasswordRequired: function(userAttributes, requiredAttributes) {
            // User was signed up by an admin and must provide new
            // password and required attributes, if any, to complete
            // authentication.

            // the api doesn't accept this field back
            delete userAttributes.email_verified;

            var newPassword = prompt('Enter new password ' ,'');

            // Get these details and call
            cognitoUser.completeNewPasswordChallenge(newPassword, userAttributes, this);
        }

    });


}

function windowLoaded() 
{
    //console.log("Loading finished");

    // Attach button listener
    var loginButton = document.getElementById("input_login");
    loginButton.addEventListener( "click", attemptLogin );
}

// Attach button listener once page loads
window.onload = windowLoaded();
