
function getParameterByName(name, url) {
    if (!url) url = window.location.href;
    name = name.replace(/[\[\]]/g, "\\$&");
    var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
        results = regex.exec(url);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, " "));
}

if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};
var auth_token = getParameterByName('auth_token');
var username = getParameterByName('username');
$('#current_username').html(username)

var service = new ReconnectingWebSocket(ws_scheme + location.host + "/service?authtoken=" + auth_token);
var boards = {};

var pieces_strategy = {
    'p': moveBlackPawn,
    'P': moveWhitePawn,
    'r': null, //moveRook,
    'R': null, //moveRook,
    'k': null,
    'K': null,
    'h': null,
    'H': null,
    'b': null,
    'B': null,
    'q': null, //moveQueen,
    'Q': null, //moveQueen
};

var pretty_pieces = {
    'p': '♟',
    'P': '♙',
    'r': '♜',
    'R': '♖',
    'k': '♚',
    'K': '♔',
    'h': '♞',
    'H': '♘',
    'b': '♝',
    'B': '♗',
    'q': '♛',
    'Q': '♕',
    ' ': ' '
}

var processing = false;

service.onopen = function() {
  console.log('service open');
  send('login', {});
};

service.onclose = function(){
    console.log('service closed');
    this.service = new WebSocket(service.url);

};

service.onmessage = function(message) {
  console.log(message.data)
  var data = JSON.parse(message.data);

  if(data.event == 'gameover') {
    alert(
      'Game is Over! \n' +
      data.data.white_username + ": " + data.data.white_score + "\n" +
      data.data.black_username + ": " + data.data.black_score
    )
  }
  if(data.event == 'update_user_list') {
    $("#input-challenge-username").empty();
    for( user in data.data.users_list ) {
      $("#input-challenge-username").append("<option value='" + data.data.users_list[user] + "'>" + data.data.users_list[user] + "</option>");
    }
  }

  if(data.event == 'ask_challenge') {
    if( confirm(data.data.username + ' challenge you to play, do you want to play with him?') ) {
      //verifySubscribeBoard(data.data.board_id);
      send('accept_challenge', { board_id: data.data.board_id });
    }
  }

  if(data.event == 'your_turn') {
    console.log('processing ' + data.data.turn_token);
    while(processing){
      console.log('processing');
    }
    processing = true;
    //verifySubscribeBoard(data.data.board_id);
    parseBoard(data.data);
    //alert('it is your turn with ' + data.data.color);
    console.log('selecting Piece!');
    if(data.data.actual_turn === 'white') {
      pieces = boards[data.data.board_id].white_pieces
    } else {
      pieces = boards[data.data.board_id].black_pieces
    }
    selectedPiece = null;
    while(!selectedPiece) {
      selectedPiece = pieces[random(pieces.length)];
      if(!selectedPiece.piece_strategy) {
        selectedPiece = null;
      }
    }
    // $('#link-view-board')[0].href = "/view?board_id=" + data.data.board_id;
    $('#input-move-board-id')[0].value = data.data.board_id;
    $('#input-move-turn-token')[0].value = data.data.turn_token;
    $("#input-move-from-row")[0].value = selectedPiece.row;
    $("#input-move-from-col")[0].value = selectedPiece.col;
    posible_move = selectedPiece.piece_strategy(data.data.actual_turn, selectedPiece.row, selectedPiece.col);
    console.log(
      'move Piece FROM' +
      ' row: '+selectedPiece.row +
      ' col: '+selectedPiece.col +
      ' TO row: '+posible_move.to_row +
      ' col: ' + posible_move.to_col
      );
    $("#input-move-to-row")[0].value = posible_move.to_row;
    $("#input-move-to-col")[0].value = posible_move.to_col;
    move();
    processing = false;
  }

  if(data.event == 'update_board') {
    board = data.data.board;
    board_id = data.data.board_id;
    //console.log(board);
    white_pieces = []
    black_pieces = []
    for(i=1; i <= 16; i++){
        for(j=1; j <= 16; j++){
            row = (16 + 4) * i;
            col = j + 1;
            cel = board.substr(row + col, 1);
            //console.log(cel);
            if( cel != ' '){
                piece = {
                  row: (i-1),
                  col: (j-1),
                  piece_strategy: pieces_strategy[cel],
                };
                if( cel === cel.toUpperCase() ) {
                  white_pieces.push(piece);
                } else {
                  black_pieces.push(piece);
                }
            }
        }
    }
    boards[board_id] = {
      white_pieces: white_pieces,
      black_pieces: black_pieces
    };
  }

};

function verifyBoard(data) {
  boards = $("#boards");
  board_div_id = "board_" + data.board_id;
  if ( $( "#" + board_div_id ).length ) {
    return;
  }
  board_container_div = $(
    "<div>" +
    "<p>board id: " + data.board_id +
    "<a href=\"/board-log/" + data.board_id + "\" class=\"btn\" target=\"blank\">View Board Log</a></p>" +
    "<p>actual turn: " + data.actual_turn + "</p>" +
    "<p>moves left: <span id=move_left_" + data.board_id + " \> </p>" +
    "</div>"
  ).appendTo(boards);
  board_div = $("<div class=\"board\" id=\"" + board_div_id + "\"></div>").appendTo(board_container_div);
  for(row=0; row < 16; row++) {
    row_div = $("<div class=\"row\"></div>").appendTo(board_div);
    if(row % 2 == 0) {
      white_cel = true;
    } else {
      white_cel = false;
    }
    for(col=0; col < 16; col++) {
      if(white_cel) {
        cell_class = "white_place";
        white_cel = false;
      } else {
        cell_class = "black_place";
        white_cel = true;
      }
      cel_div = $("<div class=\"" + cell_class + "\"></div>").appendTo(row_div);
      cel_id = board_div_id + "_" + row + "_" + col;
      cel = $("<span id=\"" + cel_id + "\" >?</span>").appendTo(cel_div);

    }
  }

}

// parseBoard({
//   'actual_turn': 'white',
//   "username": "gabriel1",
//   "move_left": 151,
//   'board_id': "78e3a67e-98a2-4c72-b8cc-774f7bcd181b",
//   'board': "rrhhbbqqkkbbhhrrrrhhbbqqkkbbhhrrpppppppppppppppppppppppp ppppppp                                                                Q  Q                                           q                                                                                "
// });

function parseBoard(data) {
  board_id = data.board_id;
  board = data.board;
  white_pieces = [];
  black_pieces = [];
  verifyBoard(data);
  console.log("B 0123456789012345");
  $("#move_left_" + board_id).html(data.move_left)
  board_div_id = "#board_" + board_id;
  for(i=0; i < 16; i++){
      row = 16 * i;
      console.log((i % 10) + " " + board.substr(row, 16))
      for(j=0; j < 16; j++){
          col = j;
          cel = board.substr(row + col, 1);
          cel_id = board_div_id + "_" + i + "_" + j;
          $(cel_id).html(pretty_pieces[cel]);
          if( cel != ' '){
              piece = {
                row: i,
                col: j,
                piece_strategy: pieces_strategy[cel],
              };
              if( cel === cel.toUpperCase() ) {
                white_pieces.push(piece);
              } else {
                black_pieces.push(piece);
              }
          }
      }
  }
  console.log("W 0123456789012345")
  boards[board_id] = {
    white_pieces: white_pieces,
    black_pieces: black_pieces
  };
}

function moveBlackPawn(color, from_row, from_col) {
  return { to_row: from_row + 1, to_col: from_col }
}
function moveWhitePawn(color, from_row, from_col) {
  return { to_row: from_row - 1, to_col: from_col }
}

function moveRook(color, from_row, from_col) {
  if( random(1) ) {
    return { to_row: from_row + random(16) * ( random(3) - 1 ) , to_col: from_col };
  } else {
    return { to_row: from_row, to_col: from_col + random(16) * ( random(3) - 1 ) };
  }
}

function moveQueen(color, from_row, from_col) {
   distance = random(8);
   vertical = random(3) - 1;
   horizontal = random(3) - 1;
   return {
     to_row: from_row + (distance * vertical),
     to_col: from_col + (distance * horizontal)
   }
 }

function verifySubscribeBoard(board_id) {
  if(board_id) {
    send('subscribe', { board_id:board_id });
  }
}

function random(base) {
  return Math.floor((Math.random() * base));
}

function move() {
  var board_id   = $("#input-move-board-id")[0].value;
  var turn_token   = $("#input-move-turn-token")[0].value;
  var from_row   = $("#input-move-from-row")[0].value;
  var from_col   = $("#input-move-from-col")[0].value;
  var to_row   = $("#input-move-to-row")[0].value;
  var to_col   = $("#input-move-to-col")[0].value;
  if(board_id && turn_token && from_row && from_col && to_row && to_col) {
    send( 'move', {
        board_id: board_id,
        turn_token: turn_token,
        from_row: parseInt(from_row),
        from_col: parseInt(from_col),
        to_row: parseInt(to_row),
        to_col: parseInt(to_col),
    });
  } else {
    console.log('missing data');
  }
}

$("#get-connected-users-button").click(function() {
  event.preventDefault();
    send('get_connected_users', {});

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


function send(action, data) {
    sendData = {
      action: action,
      data: data
    };
    console.log('sending ' + sendData);
    service.send(JSON.stringify(sendData));
    console.log('sending done ' + sendData);
}
