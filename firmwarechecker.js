let util = require('util');
let exec = util.promisify(require('child_process').exec);
let fs = require('fs');

async function check() {
	try {
		let fixLogitech = 'dwc_otq.fiq_enable=1 dwc_otg.fiq_fsm_enable=1 dwc_otg.fiq_fsm_mask=0x03';
		//let autoboot = 'sudo node /home/pi/Desktop/houston123/main.js'
		
		let pid;
		try {			
			await exec('pidof python').then((data) => {
				pid = data.stdout;
			});
		} catch (error) {
			
		}
		
		if (pid != null) {
			console.log('Python is running...');		
			pid = pid.replace('\n', '');
			pid = pid.toString().split(' ');
			for (let p of pid) {
				try {
					await exec(`sudo kill -9 ${p}`);
					console.log(`${p} was killed!`);
				} catch (error) {
					console.log(`Cant kill pid:${p}`);
				}
			}
		}

		await exec('find /home/pi/Desktop/houston123').then(() => {
			console.log('Source is ready');
        });
        await exec('sudo git reset --hard origin/master', {cwd: '/home/pi/Desktop/houston123'}).then(() => {
			console.log('Reset to branch master');
		});
		await exec('sudo git pull', {cwd: '/home/pi/Desktop/houston123'}).then(() => {
			console.log('Pull lastest version');
		});
		await fs.readFile('/boot/cmdline.txt', 'utf8', (err, data) => {
			data = data.replace('\r', '');
			data = data.replace('\n', '');			
			if (typeof data == 'string' && data.indexOf(fixLogitech) == -1) {
				data += ' ' + fixLogitech;
				exec(`echo "${data}" > 'cmdline.txt'`, {cwd: '/boot'}).then(() => {
					console.log('Fixed webcam logitech');
				});
			} else {
				console.log('Webcam logitech was fixed');
			}
		});
        await exec('sudo apt-get install -y  fswebcam').then(() => {
			console.log('Install lib fswebcam');
		});		
        await exec('sudo pip install websocket-client').then(() => {
			console.log('Install lib websocket-client');
		});
        await exec('sudo python setup.py install', {cwd: '/home/pi/Desktop/houston123/SPI-Py'}).then(() => {
			console.log('Install lib SPI');
		});
		
		exec('python ThreadRealWork_25_12_2018.py', {cwd: '/home/pi/Desktop/houston123'});
	} catch (err) {
		switch (err.cmd) {
			case 'find /home/pi/Desktop/houston123': {
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
		await exec('cd /home/pi/Desktop');
		await exec('sudo git clone https://github.com/tranvinhphuc111996/houston123.git');
		init();
	} catch (err) {
		console.log(err);
	}  
}

function reboot() {
	exec('reboot');
}

exports.update = check;
exports.reboot = reboot;
