sudo nano /etc/systemd/system/slideshow.service

[Unit]
Description=Pi Photo Slideshow
After=graphical.target

[Service]
Type=simple
User=loz
WorkingDirectory=/home/loz/slideshow
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/loz/.Xauthority
ExecStart=/usr/bin/python3 /home/loz/slideshow/slideshow.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical.target

sudo systemctl daemon-reload
sudo systemctl enable slideshow.service
sudo systemctl start slideshow.service
sudo systemctl status slideshow.service

sudo reboot
