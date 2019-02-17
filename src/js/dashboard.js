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

function getAccessToken()
{
    return getCookie("accessToken");
}

function attemptServerAdd()
{
    console.log("Attempting to add new server for monitoring");

    var dnsHostnameOrIpAddress = document.getElementById("input_new_server_address").value;

    console.log("New server hostname/IP: " + dnsHostnameOrIpAddress );

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
