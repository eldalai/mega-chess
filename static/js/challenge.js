function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}


$("#challenge-form").on("submit", function(event) {
  event.preventDefault();
    var auth_token = getParameterByName('auth_token');
    var username = $("#input-challenge-username")[0].value;
    var message = $("#input-challenge-message")[0].value;
    var data = {
        username: username,
        message: message,
        auth_token: auth_token
    };
    $.ajax({
    type: "POST",
    url: "ask_challenge",
    data: JSON.stringify(data),
    contentType: "application/json",
    complete: function(data) {
      alert(data.responseText);
    }
    });

});
