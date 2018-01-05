function putGamesToPage(output) {
  var gdict = output.split("\n");
  var buf = "";
  if (gdict[0] !== "") {
    buf += "<p>Choose a game from the list below to start watching<br><br>";
    for (var i=0; i<gdict.length; i++) {
      buf += '<a onclick="actuallyDoSocket2(\''+gdict[i]+'\')">';
      var dsplit = gdict[i].split(",");
      buf += dsplit[1]+" (Black) vs "+dsplit[2]+" (White) ["+dsplit[3]+"s]";
      buf += '</a><br>';
    }
    buf += "</p>";
  } else {
    buf += "<p>There are no games running currently.</p>";
  }
  document.getElementById('canvasContainer').innerHTML = buf;
}

function actuallyDoSocket2(data) {
  dsplit = data.split(",");
  makeSocketFromPage(HOST,PORT,dsplit[1],dsplit[2],'1000',dsplit[3],dsplit[0]);
}