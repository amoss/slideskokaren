var numThumbs = 9;
var winSize = Math.floor(numThumbs/2);
var mainScale = 1.0;

function syncThumbs()
{
  for(var i=0; i<slides.length; i++)
  {
    if(i==currentSlide)
      slides[i].style.visibility = 'visible';
    else  {
      slides[i].style.visibility = nav.style.visibility;
    }
  }
}

function makeCurrent(idx)
{
  if(idx >= slides.length || idx < 0)
    return;

  var winCenter = idx;
  console.log(idx);
  if(winCenter+winSize >= slides.length)
    winCenter = slides.length-winSize-1;
  if(winCenter-winSize <= 0)
    winCenter -= winCenter-winSize;    /* Flip polarity */
  console.log('Window ' + (winCenter-winSize) + ' .. ' + (winCenter+winSize));

  var start = winCenter-winSize, stop = winCenter+winSize;
  if(nav.style.visibility=="hidden") {
    start = idx;
    stop  = idx;
  }
  
  /* Slides before the current window */
  for(var i=0; i<start; i++)
  {
    slides[i].style.top     = -thumbHeight;
    slides[i].style.opacity = 0;
    slides[i].style.zIndex  = 0;
    slides[i].style.transform  = 'scale(' + thumbScale + ')';
    slides[i].style.webkitTransform  = 'scale(' + thumbScale + ')';
  }
  /* Slides in the window */
  for(var i=start; i<=stop; i++)
  {
    var offset = i - start;
    slides[i].style.visibility = 'visible';
    slides[i].style.opacity    = 0.8;
    slides[i].style.transform  = 'scale(' + thumbScale + ')';
    slides[i].style.webkitTransform  = 'scale(' + thumbScale + ')';
    slides[i].style.top = offset * thumbHeight + 32;
    slides[i].style.zIndex  = 4;
  }
  /* Slides after the current window */
  for(var i=stop+1; i<slides.length; i++)
  {
    slides[i].style.top     = numThumbs*thumbHeight + 32;
    slides[i].style.opacity = 0;
    slides[i].style.zIndex  = 0;
    slides[i].style.transform  = 'scale(' + thumbScale + ')';
    slides[i].style.webkitTransform  = 'scale(' + thumbScale + ')';
  }

  currentSlide = idx;
  syncThumbs();
  slides[idx].style.top = 0;
  slides[idx].style.opacity    = 1;
  //slides[idx].style.pointerEvents = "auto";
  slides[idx].style.visibility    = "visible";
  slides[idx].style.transform = 'scale(' + mainScale + ')';
  slides[idx].style.webkitTransform = 'scale(' + mainScale + ')';
  slides[idx].style.zIndex  = 2;
  slides[idx].style.visibility = 'visible';
}
window.onkeydown = function(kcode)
{
  //if(currentSlide <= 0)
  //  return;   // No slides selected
  switch(kcode.which)
  {
    case 37: //left
        makeCurrent(currentSlide-1);
      break;
    case 39: //right
        makeCurrent(currentSlide+1);
      break;
  }
}
function rescale(div, factor) 
{
  if( div.style.transform == undefined )
    div.style['-webkit-transform'] = 'scale('+factor+')';
  else 
    div.style.transform = 'scale('+factor+')';
}

thumbs = [];

function doResize()
{
  //var slides = document.getElementsByClassName('slide');
  //if( slides.length == 0) 
  //  slides = document.getElementsByClassName('slide2');
  var wScale = window.innerWidth / (slides[0].offsetWidth + 10.0);    // Inner size, fixed px pre-scale 
  var hScale = window.innerHeight / (slides[0].offsetHeight + 10.0);  // Include margins
  mainScale = Math.min(wScale,hScale);
/*  for (var i = 0; i < slides.length; i++) 
  {*/
    slides[currentSlide].style.transform = 'scale('+mainScale+')';
    slides[currentSlide].style.webkitTransform = 'scale('+mainScale+')';   // Safari sucks balls 
/*  }*/
}

function settingsButton()
{
  document.getElementById('navpanel').style.visibility = 'visible';
  syncThumbs();
  for(var i=0; i<slides.length; i++)
    slides[i].style.transition = "left 0.75s, top 0.75s, opacity 0.75";
}

function navcloseButton()
{
  document.getElementById('navpanel').style.visibility = 'hidden';
  syncThumbs();
  for(var i=0; i<slides.length; i++)
    slides[i].style.transition = "left 0s, top 0s, opacity 0.75s";
}

function rightButton()
{
  makeCurrent(currentSlide+1);
}

function leftButton()
{
  makeCurrent(currentSlide-1);
}


window.onresize = doResize;
window.onload   = function() 
{ 
  if( !window.location.search.includes("style=slideshow") )
    return;
  slides = document.getElementsByClassName('S43');
  if( slides.length == 0) 
    slides = document.getElementsByClassName('S169');
  if(slides.length < numThumbs)
  {
    winSize = Math.floor(slides.length / 2 - 0.5);  // Doesn't work for 1-2 slides.
    numThumbs = winSize*2 + 1;
  }
  for(var i=0; i<slides.length; i++)
    slides[i].style.transition = "left 0s, top 0s, opacity 0.75s";
  nav = document.getElementById('navpanel')
  nav.style.visibility = "hidden";
  currentSlide = 0;
  doResize(); 
  thumbScale  = 128.0 / slides[0].offsetWidth;
  thumbHeight = thumbScale * slides[0].offsetHeight + 4;
  makeCurrent(0);
  syncThumbs();
  for(var i=0; i<slides.length; i++)
  {
    slides[i].onclick = Function('event', 'makeCurrent('+i+')');
    slides[i].style.position = "fixed";
    slides[i].style.transition = "all 0.75s";
  }
  document.body.style.margin = "0 0 0 0";
}
