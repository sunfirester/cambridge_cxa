#!/bin/bash
# Cambridge CXA Raspberry Pi Setup Script
# Run this script with sudo

echo "1. Installing requirements..."
apt-get update
apt-get install -y v4l-utils ser2net python3

echo "2. Configuring IR overlay in config.txt..."
CONFIG_FILE="/boot/firmware/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then CONFIG_FILE="/boot/config.txt"; fi
if ! grep -q "dtoverlay=gpio-ir-tx,gpio_pin=17" "$CONFIG_FILE"; then
    echo "dtoverlay=gpio-ir-tx,gpio_pin=17" >> "$CONFIG_FILE"
fi

echo "3. Configuring ser2net (TCP RS232 Bridge)..."
cat << 'EOF' > /etc/ser2net.yaml
%YAML 1.2
---
connection: &cambridge
  accepter: tcp,5000
  connector: serialdev,/dev/ttyUSB0,9600n81,local
  options:
    kickolduser: true
EOF
systemctl restart ser2net
systemctl enable ser2net

echo "4. Setting up Python IR Bridge Server..."
mkdir -p /opt/cxa_ir
cp cxa_ir_server.py /opt/cxa_ir/
chmod +x /opt/cxa_ir/cxa_ir_server.py

cat << 'EOF' > /etc/systemd/system/cxa_ir_bridge.service
[Unit]
Description=Cambridge CXA IR Volume Bridge
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/cxa_ir/cxa_ir_server.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable cxa_ir_bridge
systemctl restart cxa_ir_bridge

echo "Setup complete! Please reboot the Pi to apply the hardware overlay."
