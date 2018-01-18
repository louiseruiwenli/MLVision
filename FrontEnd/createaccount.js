$(document).ready(function(){
  $('.usernameinfo').hide().fadeIn(1000);
  $('.camerawindow').hide();


  $('#afterusername').click(function(){
    $('.usernameinfo').hide();
    $('.camerawindow').fadeIn(1000);
  });

  var mediaOption = { audio: false, video: true};

  if (!navigator.getUserMedia) {
        navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
  }

  //navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia || navigator.oGetUserMedia;

  if (!navigator.getUserMedia){
      alert('getUserMedia not supported in this browser.');
  }

  navigator.getUserMedia(mediaOption, success, function(e) {
      console.log(e);
  });



});



function success(stream){
  var video = document.querySelector("#videoElement");
  video.src = window.URL.createObjectURL(stream);
}
