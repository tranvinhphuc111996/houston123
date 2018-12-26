let socket = require('socket.io-client')('https://houston123.ddns.net');
let firmwarechecker = require('./firmwarechecker');

socket.on('connect', () => {
	console.log('Connected to server houston123.ddns.net');
	socket.emit('kiem-tra-ket-noi');
});
socket.on('ket-noi-thanh-cong', (data) => {
    socket.emit('gan-ten-cho-socket', {username: 'DIATK001', password: ''});
});
socket.on('gan-ten-cho-socket-thanh-cong', () => {
	console.log('Gan ten thanh cong');
	firmwarechecker.checkConnect();
});
socket.on('disconnect', () => {
    console.log('Loss connected to server houston123.ddns.net');
});