function putGamesToPage(output) {
  var gdict = output.split("\n");
  var buf = "<button onclick=\"ajaxConfig('./list/games', putGamesToPage);\">Refresh list</button>";
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
  document.getElementById('player-selection-text').innerHTML = buf;
}

function wsPutGamesToPage(data) {
  if (data.type !== "list_reply") {
    console.log("Wrong message type received! Not trying to parse");
    return;
  }
  var room_list = data["room_list"];
  var buf = "<button onclick=\"websocketConfig('/list/games', wsPutGamesToPage);\">Refresh list</button>";
  var gbuf = "";
  for (var id in room_list) {
    // isn't Javascript amazing?
    if (room_list.hasOwnProperty(id)) {
      var black = room_list[id]["black"];
      var white = room_list[id]["white"];
      var timelimit = room_list[id]["timelimit"];
      gbuf += '<a onclick="makeSocketFromPage(\'' + black + +'\', \'' + white + '\', ' + timelimit + ', \'' + id + '\')">';
      gbuf += black + " (Black) vs " + white + " (White) [" + timelimit + "s]";
      gbuf += '</a><br>';
    }
  }
  if (gbuf) {
    buf += "<p>Choose a game from the list below to start watching<br><br>";
    buf += gbuf;
    buf += "</p>";
  } else {
    buf += "<p>There are no games running currently.</p>";
  }
  document.getElementById("player-selection-text").innerHTML = buf;
}

function actuallyDoSocket2(data) {
  dsplit = data.split(",");
  //                 ai1      , ai2      , timelimit, watching
  makeSocketFromPage(dsplit[1], dsplit[2], dsplit[3], dsplit[0]);
}
