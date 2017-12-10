EMPTY_NM = 0;
WHITE_NM = 1
BLACK_NM = 2;

EMPTY_CH = '.';
WHITE_CH = 'o';
BLACK_CH = '@';

EMPTY_CO = '#117711';
WHITE_CO = '#ffffff';
BLACK_CO = '#000000';

BORDER_CO    = '#663300';
HIGHLIGHT_CO = '#fff700';
GOODMOVE_CO  = '#33ccff';

WHITE_IMG = new Image();
WHITE_IMG.src = './images/white.png';
BLACK_IMG = new Image();
BLACK_IMG.src = './images/black.png';

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

function addPieces(rCanvas, bSize, bArray, un, bd, sq) {
  rCanvas.board = [];

  for(var y=0; y<bSize; y++){
    for(var x=0; x<bSize; x++){
      var index = bSize*y+x;
      var toAdd = null;
      //if (bArray[index]===EMPTY_NM){
      //  toAdd = new RRect(un*x+bd, un*y+bd, sq, sq, EMPTY_CO);
      //}
      if (bArray[index] === WHITE_NM) {
        toAdd = new RImg(un*x+bd, un*y+bd, sq, sq, WHITE_IMG);
      }
      else if (bArray[index] === BLACK_NM) {
        toAdd = new RImg(un*x+bd, un*y+bd, sq, sq, BLACK_IMG);
      }
      
      if (toAdd !== null) {
        rCanvas.add(toAdd);
        rCanvas.board[index] = toAdd;
      }
    }
  }
}

function countPieces(bSize, bArray) {
  var bCount = 0;
  var wCount = 0;
  
  for(var y=0; y<bSize; y++){
    for(var x=0; x<bSize; x++){
      var index = bSize*y+x;
      if (bArray[index] === WHITE_NM) {
        wCount++;
      }
      else if (bArray[index] === BLACK_NM) {
        bCount++;
      }
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
  return inBounds(x, y, bSize) && getSpot(x, y, board, bSize) === player;
}

function addPossibleMoves(rCanvas, bSize, bArray, tomove, un, bd, sq) {
  for (var y=0; y<bSize; y++) {
    for (var x=0; x<bSize; x++) {
      if (getSpot(x, y, bArray, bSize) === EMPTY_NM) {
        var badspot = true;
        for (var dy=-1; dy<2 && badspot; dy++) {
          for (var dx=-1; dx<2 && badspot; dx++) {
            if (!(dx === 0 && dy === 0) && findBracket(x, y, tomove, bArray, bSize, dx, dy)) {
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

function drawBoard(rCanvas, bSize, bArray, tomove){
  var rc = Math.min(rCanvas.rWidth, rCanvas.rHeight);
  var bd = rc/(11*bSize+1); //from sq*s+bd*(s+1)=w, sq=10*bd
  var sq = 10*bd;
  var un = bd+sq;

  rCanvas.bd = bd;
  rCanvas.sq = sq;
  rCanvas.un = un;

  rCanvas.objects = [];
  rCanvas.add(rCanvas.fullbg);

  addBorders(rCanvas, bSize, un, bd, rc);
  addPieces(rCanvas, bSize, bArray, un, bd, sq);
  addPossibleMoves(rCanvas, bSize, bArray, tomove, un, bd, sq);
  
  rCanvas.add(rCanvas.select);
  
  rCanvas.add(rCanvas.textbg);
  rCanvas.add(rCanvas.black);
  rCanvas.add(rCanvas.white);
    
  var counts = countPieces(bSize, bArray);
  // add code to show player scores as well
  rCanvas.black.text = rCanvas.black.text.split(':')[0]+': '+counts[BLACK_NM].toString();
  rCanvas.white.text = rCanvas.white.text.split(':')[0]+': '+counts[WHITE_NM].toString();
  if(tomove === BLACK_NM){
    rCanvas.black.text = '('+rCanvas.black.text+')';
  }
  else if(tomove === WHITE_NM){
    rCanvas.white.text = '('+rCanvas.white.text+')';
  }
  rCanvas.draw();
  rCanvas.lBSize = bSize;
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

function init(socket, delay, port1, port2, timelimit){
  document.getElementById('canvasContainer').innerHTML =
    '<canvas id="canvas" width="890" height="1000"></canvas>';

  var canvas = document.getElementById('canvas');
  var gWidth = canvas.width;
  var gHeight = canvas.height;

  resize(canvas, gWidth, gHeight);
  var rCanvas = new RCanvas(canvas, gWidth, gHeight);

  var gap = rCanvas.rHeight - rCanvas.rWidth;
  rCanvas.fullbg = new RRect(0, 0, rCanvas.rWidth, rCanvas.rHeight, EMPTY_CO, 1.0);
  rCanvas.textbg = new RRect(0, rCanvas.rWidth, rCanvas.rWidth, rCanvas.rHeight-rCanvas.rWidth, '#808080', 1.0);
  rCanvas.black = new RText(0, rCanvas.rHeight-gap*2/5,'Black',gap*2/5,'Roboto Mono',BLACK_CO);
  rCanvas.white = new RText(rCanvas.rWidth/2,rCanvas.rHeight-gap*2/5,'White',gap*2/5,'Roboto Mono',WHITE_CO);

  var selected = new RRect(0, 0, 1, 1, HIGHLIGHT_CO, 0.4);
  rCanvas.select = selected;

  drawBoard(rCanvas,13,[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 2, 1, 1, 2, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1,1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]);

  window.addEventListener('resize', function(){
    resize(canvas, gWidth, gHeight);
    rCanvas.resize();
  });
  function augmentedMouseMove(event) {
    rCanvas.handleMouseMove(event);
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
  document.addEventListener('mouseup', function(){rCanvas.handleMouseUp();});
  document.addEventListener('mousedown',function(){rCanvas.handleMouseDown();});
  document.addEventListener('touchmove', augmentedMouseMove);
  document.addEventListener('touchend', function(){rCanvas.handleMouseUp();});
  document.addEventListener('touchstart',function(){rCanvas.handleMouseDown();});

  rCanvas.resize();
  socket.emit('prequest',{black:port1,white:port2,tml:timelimit});
  socket.on('reply', function(data){
    rCanvas.black.text = data.black;
    rCanvas.white.text = data.white;
    drawBoard(rCanvas, parseInt(data.bSize), bStringToBArray(data.board), CH2NM[data.tomove]);
  });
  rCanvas.clickEvent = function(){
    var olc = this.lastClicked;
    var cy = Math.floor(rCanvas.my / rCanvas.un);
    var cx = Math.floor(rCanvas.mx / rCanvas.un);
    if (cx >= 0 && cx < rCanvas.lBSize && cy >= 0 && cy < rCanvas.lBSize){
      this.lastClicked = cy * (this.lBSize+2) + cx + 3 + this.lBSize;
    }
    if (olc === -1){
      console.log('sent move '+rCanvas.lastClicked);
      socket.emit('movereply', {move:rCanvas.lastClicked.toString()});
    }
  };

  socket.on('moverequest', function(){
    console.log('move requested');
    rCanvas.lastClicked = -1;
  });
  window.setInterval(function(){socket.emit('refresh',{});console.log('refreshed');}, delay);
}

function makeSocketFromPage(addr, port, port1, port2, delay, timelimit){
  var socket;
  if (LOCAL_COPY) {
    socket = io('http://localhost:'+port);
  } else {
    socket = io('https://'+addr+':'+port,{path:'/othello/socket.io/'});
  }
  console.log('made socket');
  var delay = parseInt(delay);
  init(socket, delay, port1, port2, timelimit);
  console.log('finished initing socket');
}
