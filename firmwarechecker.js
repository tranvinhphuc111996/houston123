let util = require('util');
let exec = util.promisify(require('child_process').exec);
let fs = require('fs');

async function check() {
	try {
		let fixLogitech = 'dwc_otq.fiq_enable=1 dwc_otg.fiq_fsm_enable=1 dwc_otg.fiq_fsm_mask=0x03';

		await exec('find /home/pi/Desktop/TimeKeeper/houston123').then(() => {
			console.log('Source is ready');
        });
		await exec('git pull', {cwd: '/home/pi/Desktop/TimeKeeper/houston123'}).then(() => {
			console.log('Pull lastest version');
		});
		await fs.readFile('/boot/cmdline.txt', 'utf8', (err, data) => {
			if (typeof data == 'string' && data.indexOf(fixLogitech) == -1) {
				data += ' ' + fixLogitech;
				exec(`echo "${data}" > 'cmdline.txt'`, {cwd: '/boot'}).then(() => {
					console.log('Fixed webcam logitech');
				});
			} else { 
				console.log('Webcam logitech was fixed');
			}
		});
        await exec('apt-get install fswebcam').then(() => {
			console.log('Install lib fswebcam');
        });
        await exec('python setup.py install', {cwd: '/home/pi/Desktop/TimeKeeper/houston123/SPI-Py'}).then(() => {
			console.log('Install lib SPI');
        });
        await exec('pip install websocket-client').then(() => {
			console.log('Install lib websocket-client');
		});
		exec('python ThreadRealWork_25_12_2018.py', {cwd: '/home/pi/Desktop/TimeKeeper/houston123'});
	} catch (err) {
		switch (err.cmd) {
			case 'find /home/pi/Desktop/TimeKeeper/houston123': {
				gitClone();
			} break;
			default:
				console.log(err)
		}
	}  
}

async function gitClone() {
	try {
		console.log('Clone project TimeKeeper');		
		await exec('cd /home/pi/Desktop/TimeKeeper');
		await exec('git clone https://github.com/tranvinhphuc111996/houston123.git');
		init();
	} catch (err) {
		console.log(err);
	}  
}

exports.checkConnect = check;