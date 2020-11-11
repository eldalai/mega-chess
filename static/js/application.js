
$("#register-form").on("submit", function(event) {
  event.preventDefault();
  var username = $("#input-register-username")[0].value;
  var password = $("#input-register-password")[0].value;
  var email = $("#input-register-email")[0].value;
  var data = {
      username: username,
      password: password,
      email: email
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
      $('#link-challenge')[0].href = "/challenge?auth_token=" + auth_token + "&username=" + username;
      $('#link-tournaments')[0].href = "/tournaments?auth_token=" + auth_token;
    }
  });
});
