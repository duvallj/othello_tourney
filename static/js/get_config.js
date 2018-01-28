HOST = "othello.tjhsst.edu";
PORT = "443";

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

function putConfigToPage(output){
  output += '\nYourself'
  pdict = output.split('\n');
  //console.log(output);
  buf = 'Black: <select id="ai1" placeholder="Player 1">';
  buf += '<option value="">Player 1</option>'
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br>White: <select id="ai2" placeholder="Player 2">';
  buf += '<option value="">Player 2</option>'
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br>';
  buf += 'Time limit (secs): <input type="number" id="tml" value="5"/><br><br>'
  buf += '<button onclick="actuallyDoSocket();">Start Match!</button>'
  document.getElementById('player-selection-text').innerHTML = buf;
  $("#ai1").selectize();
  $("#ai2").selectize();
};

function actuallyDoSocket(){
  var port1 = document.getElementById('ai1').value;
  var port2 = document.getElementById('ai2').value;
  var timelimit = document.getElementById('tml').value;
  makeSocketFromPage(HOST,PORT,port1,port2,'1000',timelimit,false);
};
