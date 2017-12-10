function RCanvas(canvasObj, rWidth, rHeight){
  this.canvas = canvasObj;
  this.ctx = this.canvas.getContext('2d');
  this.rWidth = rWidth;
  this.rHeight = rHeight;
  this.wFactor = this.canvas.width / this.rWidth;
  this.hFactor = this.canvas.height / this.rHeight;
  this.objects = [];
  this.draw = function(){
    for(var obj in this.objects){
      if (this.objects.hasOwnProperty(obj)){
        this.objects[obj].draw(this.ctx,this.wFactor,this.hFactor);
      }
    }
  };
  this.resize = function(){
    this.wFactor = this.canvas.width / this.rWidth;
    this.hFactor = this.canvas.height / this.rHeight;
    this.draw();
  };
  this.add = function(obj){
    this.objects[this.objects.length] = obj;
  };
  this.mx = 0;
  this.my = 0;
  this.getMousePos = function(event) {
    // "stolen" from stackoverflow

    var dot, eventDoc, doc, body, pageX, pageY;

    event = event || window.event; // IE-ism

    // If pageX/Y aren't available and clientX/Y are,
    // calculate pageX/Y - logic taken from jQuery.
    // (This is to support old IE)
    if (event.pageX == null && event.clientX != null) {
        eventDoc = (event.target && event.target.ownerDocument) || document;
        doc = eventDoc.documentElement;
        body = eventDoc.body;
        event.pageX = event.clientX +
            (doc && doc.scrollLeft || body && body.scrollLeft || 0) -
            (doc && doc.clientLeft || body && body.clientLeft || 0);
        event.pageY = event.clientY +
            (doc && doc.scrollTop  || body && body.scrollTop  || 0) -
            (doc && doc.clientTop  || body && body.clientTop  || 0 );
    }
    this.mx = (event.pageX - this.canvas.getBoundingClientRect().left) / this.wFactor;
    this.my = (event.pageY - this.canvas.getBoundingClientRect().top) / this.hFactor;
  }
  this.lBSize = 1;
}

function RRect(x,y,width,height,fill,alpha){
  this.x = x;
  this.y = y;
  this.width = width;
  this.height = height;
  this.fill = fill;
  this.alpha = alpha;
  this.draw = function(ctx, wFactor, hFactor){
    ctx.fillStyle = this.fill;
    ctx.globalAlpha = this.alpha;
    ctx.fillRect(this.x*wFactor, this.y*hFactor, this.width*wFactor, this.height*hFactor);
    ctx.globalAlpha = 1.0;
  };
}

function RText(x,y,text,size,font,fill){
  this.x = x;
  this.y = y;
  this.text = text;
  this.size = size;
  this.font = font;
  this.fill = fill;
  this.draw = function(ctx,wFactor,hFactor){
    ctx.fillStyle = this.fill;
    ctx.font = Math.floor((hFactor+wFactor)/2*size).toString()+'px '+this.font;
    ctx.fillText(this.text,this.x*wFactor,this.y*hFactor);
  };
}

function RImg(x,y,width,height,image){
  this.x = x;
  this.y = y;
  this.width = width;
  this.height = height;
  this.draw = function(ctx, wFactor, hFactor){
    ctx.drawImage(image,this.x*wFactor, this.y*hFactor, this.width*wFactor, this.height*hFactor);
  };
}
