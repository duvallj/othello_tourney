EMPTY_NM = 0;
WHITE_NM = 1
BLACK_NM = 2;

EMPTY_CH = '.';
WHITE_CH = 'o';
BLACK_CH = '@';

EMPTY_CO = '#117711';
WHITE_CO = '#ffffff';
BLACK_CO = '#000000';
BORDER_CO = '#663300';

WHITE_IMG = new Image();
WHITE_IMG.src = '../images/white.png';
BLACK_IMG = new Image();
BLACK_IMG.src = '../images/black.png';

CH2NM = {};
CH2NM[EMPTY_CH] = EMPTY_NM;
CH2NM[WHITE_CH] = WHITE_NM;
CH2NM[BLACK_CH] = BLACK_NM;

NM2CO = [];
NM2CO[EMPTY_NM] = EMPTY_CO;
NM2CO[WHITE_NM] = WHITE_CO;
NM2CO[BLACK_NM] = BLACK_CO;

function drawBoard(rCanvas, bSize, bArray){
  if(bSize === rCanvas.bSize) {
    for(var i=0; i<bSize*bSize; i++){
      rCanvas.board[i].fill = NM2CO[bArray[i]];
    }
  } else {
    var bdWidth = rCanvas.rWidth/(11*bSize+1); //from sq*s+bd*(s+1)=w, sq=10*bd
    var bdHeight = rCanvas.rHeight/(11*bSize+1);
    var bd = Math.min(bdWidth,bdHeight);
    var rc = Math.min(rCanvas.rWidth,rCanvas.rHeight);
    var sq = 10*bd;
    var un = bd+sq;

    rCanvas.objects = [];
    rCanvas.add(new RRect(0,0,rCanvas.rWidth,rCanvas.rHeight,EMPTY_CO));

    for(var i=0; i<=bSize; i++){
      rCanvas.add(new RRect(un*i, 0, bd, rc,BORDER_CO));
      rCanvas.add(new RRect(0, un*i, rc, bd,BORDER_CO));
    }

    rCanvas.board = [];

    for(var y=0; y<bSize; y++){
      for(var x=0; x<bSize; x++){
        var index = bSize*y+x;
        var toAdd;
        if (bArray[index]==EMPTY_NM){
          toAdd = new RRect(un*x+bd, un*y+bd, sq, sq, EMPTY_CO);
        }
        else if (bArray[index]==WHITE_NM) {
          toAdd = new RImg(un*x+bd, un*y+bd, sq, sq, WHITE_IMG);
        }
        else if (bArray[index]==BLACK_NM) {
          toAdd = new RImg(un*x+bd, un*y+bd, sq, sq, BLACK_IMG);
        }
        rCanvas.add(toAdd);
        rCanvas.board[index] = toAdd;
      }
    }
    rCanvas.add(new RRect(0,rCanvas.rWidth,rCanvas.rWidth,rCanvas.rHeight-rCanvas.rWidth,'#808080'));
    rCanvas.add(rCanvas.black);
    rCanvas.add(rCanvas.white);
  }
  // add code to show player scores as well
  var bCount = 0;
  var wCount = 0;
  for(var i=0; i<bArray.length; i++){
    if(bArray[i]==1){wCount++;}
    if(bArray[i]==2){bCount++;}
  }
  rCanvas.black.text = rCanvas.black.text.split(':')[0]+': '+bCount.toString();
  rCanvas.white.text = rCanvas.white.text.split(':')[0]+': '+wCount.toString();
  rCanvas.draw();
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

function init(socket, delay){
  document.getElementById('canvasContainer').innerHTML =
    '<canvas id="canvas" width="890" height="1000"></canvas>';
  var canvas = document.getElementById('canvas');
  var gWidth = canvas.width;
  var gHeight = canvas.height;
  resize(canvas, gWidth, gHeight);
  var rCanvas = new RCanvas(canvas, gWidth, gHeight);
  window.addEventListener('resize', function(){ resize(canvas, gWidth, gHeight);rCanvas.resize();});
  var gap = rCanvas.rHeight - rCanvas.rWidth;
  rCanvas.black = new RText(0,rCanvas.rHeight-gap*2/5,'Black',gap*2/5,'Roboto Mono',BLACK_CO);
  rCanvas.white = new RText(rCanvas.rWidth/2,rCanvas.rHeight-gap*2/5,'White',gap*2/5,'Roboto Mono',WHITE_CO);
  drawBoard(rCanvas,5,[1,1,0,1,1,1,2,0,2,1,0,0,0,0,0,2,0,0,0,2,0,2,2,2,0]);
  rCanvas.resize();
  socket.on('reply', function(data){
    rCanvas.black.text = data.black;
    rCanvas.white.text = data.white;
    drawBoard(rCanvas, parseInt(data.bSize), bStringToBArray(data.board));
    /*else if(data.type === 'win'){
      rCanvas.objects = [];
      if(data.winner === 'black'){
        rCanvas.add(new RRect(0,0,rCanvas.rWidth,rCanvas.rHeight,BLACK_CO));
        rCanvas.font = (rCanvas.rHeight/10).toString()+'px Roboto Mono'
        rCanvas.add(new RText((rCanvas.ctx.measureText('Black Wins!').width)/2,rCanvas.rHeight/2,
          'Black Wins!',rCanvas.rHeight/10,'Roboto Mono',WHITE_CO));
      }
      else if(data.winner === 'white'){
        rCanvas.add(new RRect(0,0,rCanvas.rWidth,rCanvas.rHeight,WHITE_CO));
        rCanvas.font = (rCanvas.rHeight/10).toString()+'px Roboto Mono'
        rCanvas.add(new RText((rCanvas.ctx.measureText('White Wins!').width)/2,rCanvas.rHeight/2,
          'White Wins!',rCanvas.rHeight/10,'Roboto Mono',BLACK_CO));
      }
      rCanvas.add(new RRect(0,rCanvas.rWidth,rCanvas.rWidth,rCanvas.rHeight-rCanvas.rWidth,'#808080'));
      rCanvas.add(rCanvas.black);
      rCanvas.add(rCanvas.white);
      rCanvas.draw();
    }*/
  });
  window.setInterval(function(){socket.emit('refresh',{});}, delay);
}

function makeSocketFromPage(addr, port, delay){
  var socket = io('http://'+addr+':'+port);
  console.log('made socket');
  var delay = parseInt(delay);
  init(socket, delay);
  console.log('finished initing socket');
}
