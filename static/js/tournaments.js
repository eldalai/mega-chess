
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};
var auth_token = getParameterByName('auth_token');

// var login = new ReconnectingWebSocket(ws_scheme + location.host + "/login?authtoken=" + auth_token);
var service = new ReconnectingWebSocket(ws_scheme + location.host + "/service?authtoken=" + auth_token);
var boards = {};

service.onopen = function() {
  console.log('service open');
  service.send(JSON.stringify({
    action: 'login',
    data: {}
  }));
};

service.onclose = function(){
    console.log('service closed');
    this.service = new WebSocket(service.url);

};

service.onmessage = function(message) {
  console.log(message.data)
  var data = JSON.parse(message.data);
  if(data.action == 'tournament_created') {
    alert('tournament created ' + data.data.id);    
    $('#input-add-user-tournament-tournament-id')[0].value = data.data.id;
    $('#input-start-tournament-tournament-id')[0].value = data.data.id;
  }
  if(data.action == 'update_user_list') {
    $("#input-user-add-tournament-username").empty();
    for( user in data.data.users_list ) {
      $("#input-user-add-tournament-username").append("<option value='" + data.data.users_list[user] + "'>" + data.data.users_list[user] + "</option>");
    }
  }
};

$("#create-tournament-form").on("submit", function(event) {
  event.preventDefault();
  send('create_tournament', {});
});

$("#add-user-tournament-form").on("submit", function(event) {
  event.preventDefault();
  var username   = $("#input-user-add-tournament-username")[0].value;
  var tournament_id   = $("#input-add-user-tournament-tournament-id")[0].value;
  send('add_user_to_tournament', {
    username: username,
    tournament_id: tournament_id
  });
});

$("#start-tournament-form").on("submit", function(event) {
  event.preventDefault();
  var tournament_id   = $("#input-start-tournament-tournament-id")[0].value;
  send('start_tournament', {
    tournament_id: tournament_id
  });
});

$("#get-connected-users-button").click(function() {
  event.preventDefault();
    send('get_connected_users', {});

});

function send(action, data) {
    sendData = {
      action: action,
      data: data
    };
    console.log('sending ' + sendData);
    service.send(JSON.stringify(sendData));
    console.log('sending done ' + sendData);
}
