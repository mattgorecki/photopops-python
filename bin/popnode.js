var io = require('socket.io').listen(5000);

io.sockets.on('connection', function (socket) {
  socket.send('Node.js Started');

  socket.on('button_pressed', function(data) {
	socket.broadcast.emit('button_pressed', data);
  });

  socket.on('photo_taken', function(filename) {
	socket.broadcast.emit('photo_taken', filename);
  });

  socket.on('tv_photo_taken', function(filename) {
    socket.broadcast.emit('tv_photo_taken', filename);
  });

  socket.on('log_event', function(data) {
    socket.broadcast.emit('log_event', data);
  });

});
