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
    output = 'admin:5000\nstrategy5_2019jduvall:5001'
    pairs = output.split('\n');
    pdict = {};

    for(i=0, len=pairs.length; i<len; i++){
      parts = pairs[i].split(':');
      pdict[parseInt(parts[1])] = parts[0];
    }

    pdict[-1] = 'human';

    return pdict;
}

function putConfigToPage(){
  pdict = loadConfig();
  buf = '<p>Black: <select id="ai1">';
  for (var key in pdict){
    if(pdict.hasOwnProperty(key)){
      buf += '<option value="'+key.toString()+'">'+pdict[key]+'</option>'
    }
  }
  buf += '</select><br><br>White: <select id="ai2">';
  for (var key in pdict){
    if(pdict.hasOwnProperty(key)){
      buf += '<option value="'+key.toString()+'">'+pdict[key]+'</option>'
    }
  }
  buf += '</select><br><br><button onclick="actuallyDoSocket();">Start Match!</button></p>'
  document.getElementById('canvasContainer').innerHTML = buf;
}

function actuallyDoSocket(){
  var port1 = document.getElementById('ai1').value;
  var port2 = document.getElementById('ai2').value;
  makeSocketFromPage('localhost','7531',port1,port2,'1000');
}
