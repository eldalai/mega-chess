// https://github.com/joewalnes/reconnecting-websocket/
function ReconnectingWebSocket(a){function f(g){c=new WebSocket(a);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","attempt-connect",a)}var h=c;var i=setTimeout(function(){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","connection-timeout",a)}e=true;h.close();e=false},b.timeoutInterval);c.onopen=function(c){clearTimeout(i);if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onopen",a)}b.readyState=WebSocket.OPEN;g=false;b.onopen(c)};c.onclose=function(h){clearTimeout(i);c=null;if(d){b.readyState=WebSocket.CLOSED;b.onclose(h)}else{b.readyState=WebSocket.CONNECTING;if(!g&&!e){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onclose",a)}b.onclose(h)}setTimeout(function(){f(true)},b.reconnectInterval)}};c.onmessage=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onmessage",a,c.data)}b.onmessage(c)};c.onerror=function(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","onerror",a,c)}b.onerror(c)}}this.debug=false;this.reconnectInterval=1e3;this.timeoutInterval=2e3;var b=this;var c;var d=false;var e=false;this.url=a;this.readyState=WebSocket.CONNECTING;this.URL=a;this.onopen=function(a){};this.onclose=function(a){};this.onmessage=function(a){};this.onerror=function(a){};f(a);this.send=function(d){if(c){if(b.debug||ReconnectingWebSocket.debugAll){console.debug("ReconnectingWebSocket","send",a,d)}return c.send(d)}else{throw"INVALID_STATE_ERR : Pausing to reconnect websocket"}};this.close=function(){if(c){d=true;c.close()}};this.refresh=function(){if(c){c.close()}}}ReconnectingWebSocket.debugAll=false

var inbox = new ReconnectingWebSocket("ws://"+ location.host + "/receive");
var outbox = new ReconnectingWebSocket("ws://"+ location.host + "/submit");

inbox.onmessage = function(message) {
  var data = JSON.parse(message.data);
  $("#chat-text").append("<div class='panel panel-default'><div class='panel-heading'>" + data.handle + "</div><div class='panel-body'>" + data.text + "</div></div>");
  $("#chat-text").stop().animate({
    scrollTop: $('#chat-text')[0].scrollHeight
  }, 800);
};

// inbox.onopen
inbox.onclose = function(){
    console.log('inbox closed');
    this.inbox = new WebSocket(inbox.url);

};

outbox.onclose = function(){
    console.log('outbox closed');
    this.outbox = new WebSocket(outbox.url);
};

$("#input-form").on("submit", function(event) {
  event.preventDefault();
  var handle = $("#input-handle")[0].value;
  var text   = $("#input-text")[0].value;
  outbox.send(JSON.stringify({ handle: handle, text: text }));
  $("#input-text")[0].value = "";
});
