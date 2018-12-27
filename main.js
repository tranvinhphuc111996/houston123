let socket = require('socket.io-client')('https://houston123.ddns.net/devices/timekeeper');
let firmwarechecker = require('./firmwarechecker');
let os = require('os');

//firmwarechecker.update()

function imStillALive() {
	socket.emit('status', {status: 'keepalive', uptime: os.uptime()})
}
  
setInterval(imStillALive, 2 * 60 * 1000);

socket.on('connect', () => {
	console.log('Connected to server houston123.ddns.net');
	socket.emit('getDevicesToken');
});

socket.on('getDevicesToken', (data) => {
	console.log(data);
})

socket.on('update', (data) => {
	firmwarechecker.update()
});

socket.on('reboot', (data) => {
	socket.emit('status', {status: 'reboot'})
	firmwarechecker.reboot();
});

socket.on('disconnect', () => {
    console.log('Loss connected to server houston123.ddns.net');
});
