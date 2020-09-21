// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

var service = new ReconnectingWebSocket(ws_scheme + location.host + "/service");

service.onclose = function(){
    console.log('service closed');
    this.service = new WebSocket(service.url);

};

service.onmessage = function(message) {
  console.log(message.data)
  var data = JSON.parse(message.data);
  if(data.event == 'update_user_list') {
    $("#input-challenge-user").empty();
    for( user in data.data.users_list ) {
      $("#input-challenge-username").append("<option value='" + data.data.users_list[user] + "'>" + data.data.users_list[user] + "</option>");
    }
  }
  if(data.event == 'ask_challenge') {
    if( confirm(data.data.username + ' challenge you to play, do you want to play with him?') ) {
      send('accept_challenge', { board_id: data.data.board_id });
    }
  }
};

$("#challenge-form").on("submit", function(event) {
  event.preventDefault();
  var challenge_username   = $("#input-challenge-username")[0].value;
  var challenge_message   = $("#input-challenge-message")[0].value;
  if(challenge_username) {
    send( 'challenge', {
        username: challenge_username,
        message: challenge_message
    });
  }
});

$("#register-form").on("submit", function(event) {
  event.preventDefault();
  var username   = $("#input-register-username")[0].value;
  var password   = $("#input-register-password")[0].value;
  var data = {
      username: username,
      password: password
  };
  $.ajax({
    type: "POST",
    url: "register",
    data: JSON.stringify(data),
    contentType: "application/json",
    complete: function(data) {
      alert(data.responseText);
    }
  });
});

$("#get-token-form").on("submit", function(event) {
  event.preventDefault();
  var username   = $("#input-get-token-username")[0].value;
  var password   = $("#input-get-token-password")[0].value;
  var data = {
      username: username,
      password: password
  };
  $.ajax({
    type: "POST",
    url: "token",
    data: JSON.stringify(data),
    contentType: "application/json",
    complete: function(data) {
      alert("Your Auth token is " + data.responseText);
      auth_token = data.responseText;
      $('#spam-auth-token').html(auth_token);
      $('#auth_info').show();
      $('#link-random')[0].href = "/random?auth_token=" + auth_token + "&username=" + username;
      $('#link-tournaments')[0].href = "/tournaments?auth_token=" + auth_token;
    }
  });
});

function send(action, data) {
    service.send(JSON.stringify({
      action: action,
      data: data
    }));
}
