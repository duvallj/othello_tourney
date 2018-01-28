EMPTY_NM = 0;
WHITE_NM = 1;
BLACK_NM = 2;

EMPTY_CH = '.';
WHITE_CH = 'o';
BLACK_CH = '@';
OUTER_CH = '?';

EMPTY_CO = '#117711';
WHITE_CO = '#ffffff';
BLACK_CO = '#000000';

BORDER_CO    = '#663300';
HIGHLIGHT_CO = '#fff700';
GOODMOVE_CO  = '#33ccff';
LASTMOVE_CO  = '#ff9900';

WHITE_IMG = new Image();
WHITE_IMG.src = './static/images/white.png';
BLACK_IMG = new Image();
BLACK_IMG.src = './static/images/black.png';

BORDER_IMG = new Image();
BORDER_IMG.src = './static/images/board.png';

TILE_IMG = new Image();
TILE_IMG.src = './static/images/tile.png';

STONE_IMAGES = [];
for (var i = 0; i < 20; i++) {
  STONE_IMAGES[i] = new Image();
  STONE_IMAGES[i].src = './static/images/stones/'+i+'.png';
}

CH2NM = {};
CH2NM[EMPTY_CH] = EMPTY_NM;
CH2NM[WHITE_CH] = WHITE_NM;
CH2NM[BLACK_CH] = BLACK_NM;

NM2CO = [];
NM2CO[EMPTY_NM] = EMPTY_CO;
NM2CO[WHITE_NM] = WHITE_CO;
NM2CO[BLACK_NM] = BLACK_CO;

function addBorders(rCanvas, bSize, un, bd, rc) {
  for(var i=0; i<=bSize; i++){
    rCanvas.add(new RRect(un*i, 0, bd, rc, BORDER_CO, 1.0));
    rCanvas.add(new RRect(0, un*i, rc, bd, BORDER_CO, 1.0));
  }
}

function addPieces(rCanvas, bSize, bArray, un, bd, sq, animArray) {
  if (bSize !== rCanvas.lBSize) {
    rCanvas.imgBoard = [];
  }
  for(var y=0; y<bSize; y++){
    for(var x=0; x<bSize; x++){
      var index = bSize*y+x;
      if (bSize !== rCanvas.lBSize) {
        var new_image = new RImg(un*x+bd, un*y+bd, sq, sq, EMPTY_CO, false);
        rCanvas.imgBoard[index] = new_image;
      }
      if (rCanvas.board[index] === EMPTY_NM && bArray[index] === WHITE_NM) {
        animArray[index] = 19; //set anim to full white if piece was just placed (otherwise it would defualt to 0 and flip)
      }

      if (bArray[index] === WHITE_NM || bArray[index] === BLACK_NM) {
        rCanvas.imgBoard[index].image = STONE_IMAGES[animArray[index]];
        rCanvas.imgBoard[index].shadow =  true;
      } else if (bArray[index] == EMPTY_NM) {
        rCanvas.imgBoard[index].image = undefined; //TILE_IMG; //tile image doesn't match board
        rCanvas.imgBoard[index].shadow =  false;
      }
      
      rCanvas.board[index] = bArray[index];
      rCanvas.add(rCanvas.imgBoard[index]);
    }
  }
}

function countPieces(bSize, bArray) {
  var bCount = 0; var wCount = 0;
  for(var i=0; i<bSize*bSize; i++){
    if (bArray[i] === WHITE_NM) {
      wCount++;
    }
    else if (bArray[i] === BLACK_NM) {
      bCount++;
    }
  }
  var counts = [];
  counts[BLACK_NM] = bCount;
  counts[WHITE_NM] = wCount;
  return counts;
}

function inBounds(spotx, spoty, bSize) {
  return 0 <= spotx && spotx < bSize && 0 <= spoty && spoty < bSize;
}

function getSpot(spotx, spoty, board, bSize) {
  return board[spoty*bSize+spotx];
}

function findBracket(spotx, spoty, player, board, bSize, dirx, diry) {
  var x = spotx + dirx;
  var y = spoty + diry;
  opp = 3 - player;
  
  if (!inBounds(x, y, bSize) || getSpot(x, y, board, bSize) === player) {
    return false;
  }
  
  while (inBounds(x, y, bSize) && getSpot(x, y, board, bSize) === opp) {
    x += dirx;
    y += diry;
  }
  return {good:(inBounds(x, y, bSize) && getSpot(x, y, board, bSize) === player), bx: x, by: y};
}

function addPossibleMoves(rCanvas, bSize, bArray, tomove, un, bd, sq) {
  for (var y=0; y<bSize; y++) {
    for (var x=0; x<bSize; x++) {
      if (getSpot(x, y, bArray, bSize) === EMPTY_NM) {
        var badspot = true;
        for (var dy=-1; dy<2 && badspot; dy++) {
          for (var dx=-1; dx<2 && badspot; dx++) {
            if (!(dx === 0 && dy === 0) && findBracket(x, y, tomove, bArray, bSize, dx, dy).good) {
              badspot = false;
            }
          }
        }
        if (!badspot) {
          rCanvas.add(new RRect(un*x+bd, un*y+bd, sq, sq, GOODMOVE_CO, 0.4));
        }
      }
    }
  }
}

function addTiles(rCanvas, bSize, bArray, un, bd, sq) {
  for (var y=0; y<bSize; y++) {
    for (var x=0; x<bSize; x++) {
      rCanvas.add(new RImg(un*x+bd/2, un*y+bd/2, sq+bd, sq+bd, TILE_IMG));
    }
  }
}

function makeFlips(x, y, rCanvas, bSize, bArray, tomove) {
  var good = false;
  for (var dy=-1; dy<2; dy++) {
    for (var dx=-1; dx<2; dx++) {
      if (!(dx === 0 && dy === 0)) {
        bracketObj = findBracket(x, y, tomove, bArray, bSize, dx, dy);
        if (bracketObj.good) {
          var cx = x;
          var cy = y;
          good = true;
          while (cx !== bracketObj.bx || cy !== bracketObj.by) {
            bArray[cy*bSize+cx] = tomove;
            cx += dx;
            cy += dy;
          }
        }
      }
    }
  }
  return good;
}

function startAnimation(rCanvas, animArray) {
  var interval = setInterval(function() {
    var stable = true;
    
    for (var i=0; i<rCanvas.lBSize*rCanvas.lBSize; i++) {
      if (rCanvas.board[i] === BLACK_NM && animArray[i] > 0) {
        animArray[i] -= 1;
        rCanvas.imgBoard[i].image = STONE_IMAGES[animArray[i]];
        stable = false;
      }
      else if (rCanvas.board[i] === WHITE_NM && animArray[i] < 19) {
        animArray[i] += 1;
        rCanvas.imgBoard[i].image = STONE_IMAGES[animArray[i]];
        stable = false;
      }
    }
    
    if (stable) {
      clearInterval(interval);
    } else {
      rCanvas.draw();
    }
  },16);
}

function drawBoard(rCanvas, bSize, bArray, tomove, animArray){
  console.log('redrawing board');
  var rc = Math.min(rCanvas.rWidth, rCanvas.rHeight);
  var bd = rc/(11*bSize+1); //from sq*s+bd*(s+1)=w, sq=10*bd
  var sq = 10*bd;
  var un = bd+sq;

  rCanvas.bd = bd;
  rCanvas.sq = sq;
  rCanvas.un = un;

  rCanvas.objects = [];
  
  rCanvas.add(rCanvas.fullbg);
  //addBorders(rCanvas, bSize, un, bd, rc);

  addTiles(rCanvas, bSize, bArray, un, bd, sq);

  rCanvas.add(rCanvas.lastmove);
  
  addPieces(rCanvas, bSize, bArray, un, bd, sq, animArray);
  addPossibleMoves(rCanvas, bSize, bArray, tomove, un, bd, sq);
  rCanvas.add(rCanvas.select);
  
  /*rCanvas.add(rCanvas.textbg);
  rCanvas.add(rCanvas.black);
  rCanvas.add(rCanvas.white);*/
    
  var counts = countPieces(bSize, bArray);
  rCanvas.black.innerHTML = rCanvas.black_name+': '+counts[BLACK_NM].toString();
  rCanvas.white.innerHTML = rCanvas.white_name+': '+counts[WHITE_NM].toString();
  if(tomove === BLACK_NM){
    rCanvas.black.innerHTML = ' (*) '+rCanvas.black.innerHTML;
  }
  else if(tomove === WHITE_NM){
    rCanvas.white.innerHTML = rCanvas.white.innerHTML+' (*) ';
  }
  rCanvas.draw();
  rCanvas.lBSize = bSize;
  startAnimation(rCanvas, animArray);
}

function bStringToBArray(bString){
  bString = bString.replace(/\?/g, '');
  var bArray = [];
  for(var i=0; i<bString.length; i++){
    bArray[i] = CH2NM[bString.charAt(i)];
  }
  return bArray;
}

function resize(canvas, gWidth, gHeight){
  var availWidth = canvas.parentNode.offsetWidth*9/10;
  var availHeight = (window.innerHeight - canvas.parentNode.offsetTop)*9/10;
  if(availWidth*gHeight < availHeight*gWidth){
    canvas.width = availWidth;
    canvas.height = canvas.width * gHeight / gWidth;
  }
  else{
    canvas.height = availHeight;
    canvas.width = canvas.height * gWidth / gHeight;
  }
}

function init(socket, delay, port1, port2, timelimit, watching){
  document.getElementById('canvasContainer').style.display = "";
  document.getElementById('player-selection-text').style.display = "none";

  var canvas = document.getElementById('canvas');
  var gWidth = 1000;
  var gHeight = 1000;

  //resize(canvas, gWidth, gHeight);
  var rCanvas = new RCanvas(canvas, gWidth, gHeight);
  rCanvas.resize();
  window.addEventListener('resize', function(){
    //resize(canvas, gWidth, gHeight);
    rCanvas.resize();
  });

  //var gap = rCanvas.rHeight - rCanvas.rWidth;
  rCanvas.fullbg = new RImg(
    0, 0, 
    rCanvas.rWidth, rCanvas.rWidth, 
    BORDER_IMG
  );
  /*rCanvas.textbg = new RRect(
    0, rCanvas.rWidth, 
    rCanvas.rWidth, gap, 
    '#805229', 1.0
  );
  rCanvas.black = new RText(
    0, rCanvas.rHeight-gap*2/5,
    'Black',
    gap*2/5, 'Roboto Mono',
    BLACK_CO
  );
  rCanvas.white = new RText(
    rCanvas.rWidth/2,rCanvas.rHeight-gap*2/5,
    'White',
    gap*2/5,'Roboto Mono',
    WHITE_CO
  );*/
  rCanvas.black = document.getElementById("player-black");
  rCanvas.white = document.getElementById("player-white");
  
  var selected = new RRect(0, 0, 1, 1, HIGHLIGHT_CO, 0.4);
  rCanvas.select = selected;
  
  var lastmove = new RRect(0, 0, 1, 1, LASTMOVE_CO, 0.4);
  rCanvas.lastmove = lastmove;
  
  rCanvas.board = [];
  rCanvas.imgBoard = [];
  var animArray = []
  var dSize = 8;
  for (var i=0; i<dSize*dSize; i++) {
    rCanvas.board[i] = 0;
    animArray[i] = 0;
  }
  rCanvas.lBSize = 0;

  rCanvas.black_name = "Loading "+port1+"...";
  rCanvas.white_name = "Loading "+port2+"...";
  drawBoard(rCanvas, dSize, rCanvas.board, BLACK_NM, animArray);
  
  function augmentedMouseMove(event) {
    rCanvas.getMousePos(event);
    var cy = Math.floor(rCanvas.my / rCanvas.un);
    var cx = Math.floor(rCanvas.mx / rCanvas.un);
    var ox = selected.x;
    var oy = selected.y;
    selected.x = rCanvas.un*cx+rCanvas.bd;
    selected.y = rCanvas.un*cy+rCanvas.bd;
    selected.width = rCanvas.sq;
    selected.height = rCanvas.sq;
    if(ox !== selected.x || oy !== selected.y){
      rCanvas.draw();
    }
  }
  document.addEventListener('mousemove', augmentedMouseMove);

  clickHandler = function(event){
    augmentedMouseMove(event);
    var olc = rCanvas.lastClicked;
    var cy = Math.floor(rCanvas.my / rCanvas.un);
    var cx = Math.floor(rCanvas.mx / rCanvas.un);
    if (cx >= 0 && cx < rCanvas.lBSize && cy >= 0 && cy < rCanvas.lBSize){
      rCanvas.lastClicked = cy * (rCanvas.lBSize+2) + cx + 3 + rCanvas.lBSize;
    }
    if (olc === -1){
      console.log('touched spot '+rCanvas.lastClicked);
      var resultGood = rCanvas.board[cy*rCanvas.lBSize+cx]===EMPTY_NM && makeFlips(cx, cy, rCanvas, rCanvas.lBSize, rCanvas.board, rCanvas.tomove);
      if (resultGood) {
        lastmove.x = rCanvas.un*cx+rCanvas.bd;
        lastmove.y = rCanvas.un*cy+rCanvas.bd;
        lastmove.width = rCanvas.sq;
        lastmove.height = rCanvas.sq;
        if (rCanvas.tomove === WHITE_NM) { animArray[cy*rCanvas.lBSize+cx] = 19; }
        drawBoard(rCanvas, rCanvas.lBSize, rCanvas.board, 3 - rCanvas.tomove, animArray);
        console.log('sending move');
        socket.emit('movereply', {move:rCanvas.lastClicked.toString()});
      } else {
        rCanvas.lastClicked = -1;
      }
    }
  };
  
  if (!watching) {
    socket.emit('prequest',{black:port1,white:port2,tml:timelimit});
    document.addEventListener('click', clickHandler);
  }
  else {
    socket.emit('wrequest', {'watching': watching});
  }
  
  socket.on('reply', function(data){
    rCanvas.black_name = data.black;
    rCanvas.white_name = data.white;
    rCanvas.tomove = CH2NM[data.tomove];
    var bArray = bStringToBArray(data.board);
    var bSize = parseInt(data.bSize);
    if (bSize === rCanvas.lBSize) {
      for (var cx=0; cx<bSize; cx++) {
        for (var cy=0; cy<bSize; cy++) {
          var index = cy*bSize+cx;
          if (rCanvas.board[index] === EMPTY_NM && bArray[index] !== EMPTY_NM) {
            lastmove.x = rCanvas.un*cx+rCanvas.bd;
            lastmove.y = rCanvas.un*cy+rCanvas.bd;
            lastmove.width = rCanvas.sq;
            lastmove.height = rCanvas.sq;
          }
        }
      }
    }
    drawBoard(rCanvas, bSize, bArray, CH2NM[data.tomove], animArray);
  });

  socket.on('moverequest', function(){
    console.log('move requested');
    rCanvas.lastClicked = -1;
  });
  /* var refreshInterval;
  if (watching) {
    refreshInterval = window.setInterval(function(){socket.emit('refresh',{"watching": watching});console.log('refreshed');}, delay);
  } else {
    refreshInterval = window.setInterval(function(){socket.emit('refresh',{});console.log('refreshed');}, delay);
  } */

  /* function alwaysDraw() {
    drawBoard(rCanvas, rCanvas.lBSize, rCanvas.board, rCanvas.tomove, animArray);
    requestAnimationFrame(alwaysDraw);
  }
  requestAnimationFrame(alwaysDraw); */
  
  socket.on('gameend', function(data){
    //Clean up tasks, end socket
    //window.clearInterval(refreshInterval);
    document.removeEventListener('click', clickHandler);
    socket.disconnect();
    // Handle winner conditions
    var black_text = "";
    var white_text = "";
    if (data.winner === BLACK_CH) {
      black_text = "[Winner]\n" + black_text;
      if (data.forfeit) {
        white_text = "[Errored]\n" + white_text;
        if(data.err_msg){
            document.getElementById('canvasContainer').innerHTML = '<pre><code>' + data.err_msg + '</code></pre>';
            return;
        }
      }
    } else if (data.winner === WHITE_CH) {
      white_text = "[Winner]\n" + white_text;
      if (data.forfeit) {
        black_text = "[Errored]\n" + black_text;
        if(data.err_msg){
            document.getElementById('canvasContainer').innerHTML = '<pre><code>' + data.err_msg + '</code></pre>';
            return;
        }
      }
    } else if (data.winner === EMPTY_CH) {
      black_text = "[Tie]\n" + black_text;
      white_text = "[Tie]\n" + white_text;
    } else {
      if (data.forfeit) {
        black_text = "[Game Over]\n" + black_text;
        white_text = "[Game Over]\n" + white_text;
      } else {
        black_text = "[Server error]\n" + black_text;
        white_text = "[Server error]\n" + white_text;
      }
    }
    //Add text signifying that the game is over
    rCanvas.black.y = rCanvas.rHeight - gap*1/5;
    rCanvas.black.size = gap*3/10;
    rCanvas.white.y = rCanvas.rHeight - gap*1/5;
    rCanvas.white.size = gap*3/10;
    drawBoard(rCanvas, rCanvas.lBSize, rCanvas.board, rCanvas.tomove, animArray);
    rCanvas.add(new RText(0,rCanvas.rHeight-gap*3/5, 
      black_text,
      gap*3/10,'Roboto Mono',
      BLACK_CO
    ));
    rCanvas.add(new RText(rCanvas.rWidth/2,rCanvas.rHeight-gap*3/5,
      white_text,
      gap*3/10,'Roboto Mono',
      WHITE_CO
    ));
    rCanvas.draw();
  });
}

function makeSocketFromPage(addr, port, port1, port2, delay, timelimit, watching){
  var socket;
  if (port !== "443") {
    socket = io('http://'+addr+':'+port);
  } else {
    socket = io('https://'+addr+':'+port);
  }
  console.log('made socket');
  var delay = parseInt(delay);
  init(socket, delay, port1, port2, timelimit, watching);
  console.log('finished initing socket');
}
