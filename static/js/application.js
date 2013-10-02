var inbox = new WebSocket("ws://"+ location.host + "/receive");
var outbox = new WebSocket("ws://"+ location.host + "/submit");

inbox.onmessage = function(message) {
  var data = JSON.parse(message.data);
  $("#chat-text").append("<div class='panel panel-default'><div class='panel-heading'>" + data.handle + "</div><div class='panel-body'>" + data.text + "</div></div>");
  $("#chat-text").stop().animate({
    scrollTop: $('#chat-text')[0].scrollHeight
  }, 800);
};

inbox.onclose = function(){
    alert('inbox closed')
};

outbox.onclose = function(){
    alert('inbox closed')
};

$("#input-form").on("submit", function(event) {
  event.preventDefault();
  var handle = $("#input-handle")[0].value;
  var text   = $("#input-text")[0].value;
  outbox.send(JSON.stringify({ handle: handle, text: text }));
  $("#input-text")[0].value = "";
});
