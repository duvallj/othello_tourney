LOCAL_COPY = false;

function ajaxConfig(callback){
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
    xmlhttp.open("GET", "./ai_port_info.txt", true);
    xmlhttp.send();
};

function putConfigToPage(output){
  output += '\nYourself'
  pdict = output.split('\n');
  console.log(output);
  buf = '<p>Black: <select id="ai1">';
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br>White: <select id="ai2">';
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br>';
  buf += 'Time limit (secs): <input type="number" id="tml" value="5"/><br><br>'
  buf += '<button onclick="actuallyDoSocket();">Start Match!</button></p>'
  document.getElementById('canvasContainer').innerHTML = buf;
};

function actuallyDoSocket(){
  var port1 = document.getElementById('ai1').value;
  var port2 = document.getElementById('ai2').value;
  var timelimit = document.getElementById('tml').value;
  if (LOCAL_COPY) {
    makeSocketFromPage('localhost','10770',port1,port2,'1000',timelimit);
  } else {
    makeSocketFromPage('activities.tjhsst.edu','443',port1,port2,'1000',timelimit);
  }
};
