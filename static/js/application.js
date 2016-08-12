// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

var service = new ReconnectingWebSocket(ws_scheme + location.host + "/service");

service.onopen = function() {
  var username   = $("#input-login-username")[0].value;
  var password   = $("#input-login-password")[0].value;
  if(username && password) {
    service.send(JSON.stringify({
      action: 'login',
      data: {
        username: username,
        password: password
      }
    }));
  }
};

service.onclose = function(){
    console.log('service closed');
    this.service = new WebSocket(service.url);

};

service.onmessage = function(message) {
  console.log(message.data)
  var data = JSON.parse(message.data);
  if(data.action == 'update_user_list') {
    $("#input-challenge-user").empty();
    for( user in data.data.users_list ) {
      $("#input-challenge-username").append("<option value='" + data.data.users_list[user] + "'>" + data.data.users_list[user] + "</option>");
    }
  }
  if(data.action == 'ask_challenge') {
    if( confirm(data.data.username + ' challenge you to play, do you want to play with him?') ) {
      send('accept_challenge', { board_id: data.data.board_id });
    }
  }
  if(data.action == 'your_turn') {
    alert('it is your turn with ' + data.data.color);
    $('#input-move-board-id')[0].value = data.data.board_id;
    $('#input-move-turn-token')[0].value = data.data.turn_token;
  }
};


$("#move-form").on("submit", function(event) {
  event.preventDefault();
  var board_id   = $("#input-move-board-id")[0].value;
  var turn_token   = $("#input-move-turn-token")[0].value;
  var from_row   = parseInt($("#input-move-from-row")[0].value);
  var from_col   = parseInt($("#input-move-from-col")[0].value);
  var to_row   = parseInt($("#input-move-to-row")[0].value);
  var to_col   = parseInt($("#input-move-to-col")[0].value);
  if(board_id && turn_token && from_row && from_col && to_row && to_col) {
    send( 'move', {
        board_id: board_id,
        turn_token: turn_token,
        from_row: from_row,
        from_col: from_col,
        to_row: to_row,
        to_col: to_col,
    });
  }
});


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
  if(username) {
    send( 'register', {
        username: username,
        password: password
    });
  }
});

$("#login-form").on("submit", function(event) {
  event.preventDefault();
  var username   = $("#input-login-username")[0].value;
  var password   = $("#input-login-password")[0].value;
  if(username) {
    send('login', {
        username: username,
        password: password
    });
  }
});

function send(action, data) {
    service.send(JSON.stringify({
      action: action,
      data: data
    }));
}
