SCHEME = window.location.protocol == "https:" ? "wss": "ws";
//HOST = window.location.host;
HOST = "localhost:10771";
// PATH = SCHEME + "://" + HOST + "/ws/"
PATH = SCHEME + "://" + HOST + "/";

function ajaxConfig(path, callback){
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState === XMLHttpRequest.DONE ) {
            if (xmlhttp.status === 200) {
                callback(xmlhttp.responseText);
            }
            else {
                alert(xmlhttp.status);
            }
        }
    };
    xmlhttp.open("GET", path, true);
    xmlhttp.send();
};

// Same as the ajaxConfig, calling a callback on the first websocket
// message received and then immediately closing
// I only have to do this b/c I didn't want to mess around with any
// webserver libraries in Rust oop
function websocketConfig(path, callback) {
  var socket = new WebSocket(PATH+path);
 
  var has_received = false;

  socket.onopen = function () {
    console.log("Did open socket");
    // just in case??
    has_received = false;
  };

  socket.onmessage = function (message) {
    console.log("Got websocket message " + message.data);
    if (!has_received) {
      var data = JSON.parse(message.data);
      console.log("Calling callback on websocket data");
      callback(data);
      has_received = true;
    }
    socket.close();
  };

  socket.onclose = function () {
    if (has_received) {
      console.log("Got data successfully!");
    } else {
      console.log("Did not get any data...");
    }
  }
};

function putConfigToPage(output){
  pdict = output.split('\n');
  var player1 = me;
  if(window.localStorage.getItem("player1")){
      player1 = window.localStorage.getItem("player1");
  }
  var player2 = "";
  if(window.localStorage.getItem("player2")){
      player2 = window.localStorage.getItem("player2");
  }
  buf = 'Black: <select id="ai1" placeholder="Player 1">';
  buf += '<option value="">Player 1</option>'
  for (var i=0; i<pdict.length; i++){
    if(pdict[i] == player1){
        buf += '<option value="'+pdict[i]+'" selected>'+pdict[i]+'</option>'
    }
    else {
        buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
    }
  }
  buf += '</select><br><br>White: <select id="ai2" placeholder="Player 2">';
  buf += '<option value="">Player 2</option>'
  for (var i=0; i<pdict.length; i++){
    if(pdict[i] == player2){
        buf += '<option value="'+pdict[i]+'" selected>'+pdict[i]+'</option>'
    }
    else {
        buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
    }
  }
  buf += '</select><br><br>';
  buf += 'Time limit (secs): <input type="number" id="tml" value="5"/><br><br>'
  buf += '<button onclick="actuallyDoSocket();">Start Match!</button>'
  document.getElementById('player-selection-text').innerHTML = buf;
  $("#ai1").selectize();
  $("#ai2").selectize();
};

function actuallyDoSocket(){
  var ai_name1 = document.getElementById('ai1').value;
  var ai_name2 = document.getElementById('ai2').value;
  window.localStorage.setItem("player1", ai_name1);
  window.localStorage.setItem("player2", ai_name2);
  var timelimit = document.getElementById('tml').value;
  makeSocketFromPage(ai_name1,ai_name2,timelimit,false);
};
