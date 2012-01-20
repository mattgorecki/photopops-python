%rebase base title=title

<script src="http://:5000/socket.io/socket.io.js"></script>
<script>
var socket = io.connect('http://:5000');
  socket.on('message', function(data) {
    console.log(data);
  });

  socket.on('button_pressed', function(data) {
    console.log("easy button pressed");
    $('#main').css('background-color', 'transparent');
	$('#main').html('<img src="/photopops/download/static/images/countdown-1910x1074.gif">');

	// Show rotator after countdown finishes
	setTimeout(function() {
	  $('#main').css('background-color', '#000000');
	  $('#main').html('<img src="/photopops/download/static/images/rotator.gif">');
	}, 6000);

	// Reset Photo display timer if there is a button press before it's done.
	if (typeof pptimer === "undefined") {
	  clearTimeout(pptimer);
	}
  });

  socket.on('tv_photo_taken', function(data) {
	console.log(data);
	$('#main').css('background-color', '#000000');
	$('#main').html('<div align="center"><img src="'+ data +'"></div>');

	pptimer = setTimeout(function() {
      $('#main').html('');
      $('#main').css('background-color', 'transparent');
    }, 7000);
  });

$(document).bind('keyup', 'i', function() {
	alert("ip address");
});
</script>

<div id="main">&nbsp;</div>
