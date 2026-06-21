# Cambridge CXA Raspberry Pi Setup

This folder contains the scripts and documentation for configuring a Raspberry Pi to act as the network bridge for the Cambridge Audio CXA amplifier.

The Pi serves two roles:
1. **TCP to RS232 Bridge:** Uses `ser2net` to expose the USB-to-Serial adapter over port 5000.
2. **IR Volume Bridge:** Uses the `cxa_ir_server.py` daemon to expose a simple HTTP API on port 5001 that triggers the Pi's GPIO pins to send RC5 IR Volume commands to the amp.

## Hardware Wiring (IR Volume)
You must physically wire the Pi to the "IR In" port on the back of the amplifier.
1. Cut and strip a 3.5mm mono (or stereo) audio cable.
2. Connect the **Tip** wire to **GPIO 17** (Physical Pin 11). *(Recommended: Place a 330Ω to 1kΩ resistor inline).*
3. Connect the **Sleeve** wire to **GND** (Physical Pin 6, 9, 14, or 20).
4. *(If using a stereo cable, tape off the middle Ring wire).*

## Software Installation
If you are starting with a freshly flashed Raspberry Pi, simply copy this entire `pi_setup` folder to the Pi, and run the install script:

```bash
cd pi_setup
sudo chmod +x install.sh
sudo ./install.sh
```

## Testing
To test the IR commands locally from the Pi's command line:
```bash
# Volume Up
ir-ctl -d /dev/lirc0 -S rc5:0x1010

# Volume Down
ir-ctl -d /dev/lirc0 -S rc5:0x1011
```

To test the HTTP API:
```bash
curl http://localhost:5001/vol/up
curl http://localhost:5001/vol/down
```
