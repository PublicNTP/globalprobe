function attemptLogin()
{
    console.log("Attempting login");
    
    var submittedEmail = document.getElementById("input_email_address").value;
    var submittedPassword = document.getElementById("input_password").value;

    console.log("Checking username = \"" + submittedEmail + 
        "\", password = \"" + submittedPassword + "\"");
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
