function loadConfig() {
    var xmlhttp = new XMLHttpRequest();
    var output = '';
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == XMLHttpRequest.DONE ) {
           if (xmlhttp.status == 200) {
               output = xmlhttp.responseText;
           }
           else {
               alert('Error Code '+xmlhttp.status+' was returned while trying to accesss ai port list');
           }
        }
    };

    //xmlhttp.open("GET", "../ai_port_info.txt", true);
    //xmlhttp.send();
    output = 'admin\nstrategy5_2019jduvall'
    output += '\nhuman';
    pairs = output.split('\n');

    return pairs;
}

function putConfigToPage(){
  pdict = loadConfig();
  buf = '<p>Black: <select id="ai1">';
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br>White: <select id="ai2">';
  for (var i=0; i<pdict.length; i++){
    buf += '<option value="'+pdict[i]+'">'+pdict[i]+'</option>'
  }
  buf += '</select><br><br><button onclick="actuallyDoSocket();">Start Match!</button></p>'
  document.getElementById('canvasContainer').innerHTML = buf;
}

function actuallyDoSocket(){
  var port1 = document.getElementById('ai1').value;
  var port2 = document.getElementById('ai2').value;
  makeSocketFromPage('localhost','7531',port1,port2,'1000');
}
