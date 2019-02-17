function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i <ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function getIdentityToken()
{
    return getCookie("idToken");
}

function attemptServerAdd()
{
    console.log("Attempting to add new server for monitoring");

    var dnsHostnameOrIpAddress = document.getElementById("input_new_server_address").value;

    console.log("New server hostname/IP: " + dnsHostnameOrIpAddress );

    var identityToken = getIdentityToken();

    console.log("Identity token: " + identityToken );

    // Create add server POST and submit
    const addServerRequest = new XMLHttpRequest();
    const url='https://25zwa0yf5h.execute-api.us-east-2.amazonaws.com/dev/v1/server/add';
    addServerRequest.open("POST", url, true);
    addServerRequest.setRequestHeader("Content-type", "application/json");
    addServerRequest.setRequestHeader("Authorization", identityToken );
    addServerRequest.onreadystatechange = function() {
        if (addServerRequest.readyState == 4 && addServerRequest.status == 200) {
            console.log("Server response to add request: " + addServerRequest.responseText);

        }
    }

    var bodyPayload = { 
        "new_server": {
            "server_address": dnsHostnameOrIpAddress 
        }
    }
    addServerRequest.send(JSON.stringify(bodyPayload));

}

function addEventListeners()
{
    // Add new server button
    document.getElementById("input_button_add_server").addEventListener( "click", 
        attemptServerAdd );
}

function windowLoaded() 
{
    console.log("Loading finished");

    // Add all event listeners
    addEventListeners();

    /*
    // Pull auth token from cookie storage
    var accessToken = getAccessToken();

    console.log("We think our API acceess token is " + accessToken);
    */
}

// Attach button listener once page loads
window.onload = windowLoaded();
