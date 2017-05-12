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
      this.objects[obj].draw(this.ctx,this.wFactor,this.hFactor);
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
}

function RRect(x,y,width,height,fill){
  this.x = x;
  this.y = y;
  this.width = width;
  this.height = height;
  this.fill = fill;
  this.draw = function(ctx, wFactor, hFactor){
    ctx.fillStyle = this.fill;
    ctx.fillRect(this.x*wFactor, this.y*hFactor, this.width*wFactor, this.height*hFactor);
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
