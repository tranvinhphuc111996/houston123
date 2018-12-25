1.Fix l?i c?a RPi 3 và camera logitech.

Vào folder boot , vào file cmdline.txt copy dòng này vào

dwc_otg.lpm_enable=0 console=serial0,115200 console=tty1 root=PARTUUID=67407bf7-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles dwc_otq.fiq_enable=1 dwc_otg.fiq_fsm_enable=1 dwc_otg.fiq_fsm_mask=0x03


2. ch?y file setup trong libtest: SPI-py , socketio-client.