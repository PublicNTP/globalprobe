function attemptLogin()
{
    console.log("Attempting login");
    
    var submittedEmail = document.getElementById("input_email_address").value;
    var submittedPassword = document.getElementById("input_password").value;

    /*
    console.log("Checking username = \"" + submittedEmail + 
        "\", password = \"" + submittedPassword + "\"");
    */

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

            console.log("Successful login for user " + submittedEmail );
            /*
            var accessToken = result.getAccessToken().getJwtToken();
            //console.log("Access token: " + accessToken);
            */

            // ID token is passed in "Authorization" header for API gateway authorization
            var idToken = result.idToken.jwtToken;

            // Store ID token as cookies so we can access it after redirect
            document.cookie = "idToken=" + idToken;

            // Bounce to main dashboard (server list) page
            window.location.href = "/dashboard.html";
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
