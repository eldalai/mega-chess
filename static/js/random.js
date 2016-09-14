// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};

var service = new ReconnectingWebSocket(ws_scheme + location.host + "/service");
var boards = {};

var pieces_strategy = {
    'p': moveBlackPawn,
    'P': moveWhitePawn,
    'r': null,
    'R': null,
    'k': null,
    'K': null,
    'h': null,
    'H': null,
    'b': null,
    'B': null,
    'q': null,
    'Q': null
};
var processing = false;

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
      //verifySubscribeBoard(data.data.board_id);
      send('accept_challenge', { board_id: data.data.board_id });
    }
  }

  if(data.action == 'your_turn') {
    console.log('processing ' + data.data.turn_token);
    while(processing){
      console.log('processing');
    }
    processing = true;
    //verifySubscribeBoard(data.data.board_id);
      console.log('parseBoard');
    parseBoard(data.data.board_id, data.data.board);
    //alert('it is your turn with ' + data.data.color);
    selectedPiece = null;
    while(!selectedPiece) {
      console.log('selecting Piece');
      if(data.data.color === 'white') {
        pieces = boards[data.data.board_id].white_pieces
      } else {
        pieces = boards[data.data.board_id].black_pieces
      }
      selectedPiece = pieces[random(pieces.length)];
      if(!selectedPiece.piece_strategy) {
        selectedPiece = null;
      }

    }
    $('#input-move-board-id')[0].value = data.data.board_id;
    $('#input-move-turn-token')[0].value = data.data.turn_token;
    $("#input-move-from-row")[0].value = selectedPiece.row;
    $("#input-move-from-col")[0].value = selectedPiece.col;
      console.log('piece_strategy Piece');
    posible_move = selectedPiece.piece_strategy(data.data.color, selectedPiece.row, selectedPiece.col);
      console.log('piece_strategy Piece done');
    $("#input-move-to-row")[0].value = posible_move.to_row;
    $("#input-move-to-col")[0].value = posible_move.to_col;
    move();
    processing = false;
  }

  if(data.action == 'update_board') {
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

function parseBoard(board_id, board) {
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

function moveBlackPawn(color, from_row, from_col) {
  return { to_row: from_row + 1, to_col: from_col }
}
function moveWhitePawn(color, from_row, from_col) {
  return { to_row: from_row - 1, to_col: from_col }
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
    sendData = {
      action: action,
      data: data
    };
    console.log('sending ' + sendData);
    service.send(JSON.stringify(sendData));
    console.log('sending done ' + sendData);
}
