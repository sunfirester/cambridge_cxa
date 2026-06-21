# Home Assistant Custom Component for Cambridge Audio CXA 61/81

This custom component enables local control of the Cambridge Audio CXA 61 and CXA 81 amplifiers in Home Assistant.

## Architecture

Cambridge Audio CXA amplifiers expose an RS232 port for control, but unfortunately, they do not support reliable volume control over RS232. To overcome this limitation, this integration relies on a **Raspberry Pi** acting as a hybrid bridge:

1. **Serial Bridge (ser2net):** Handles standard commands (Power, Mute, Source selection) by passing TCP commands on port 5000 to the RS232-to-USB adapter connected to the amplifier.
2. **IR Bridge (HTTP API):** Handles volume control (Up/Down) by receiving HTTP requests on port 5001 and triggering a GPIO pin wired directly into the amplifier's "IR In" port on the back.

## Hardware & Pi Setup

You must configure a Raspberry Pi to sit between Home Assistant and the amplifier.

Please refer to the [pi_setup/README.md](pi_setup/README.md) file in this repository for full hardware wiring instructions and the automated Raspberry Pi installation script.

## Installation

### Method 1: HACS (Recommended)
1. Open HACS in Home Assistant.
2. Add a custom repository: `sunfirester/cambridge_cxa` (Integration).
3. Install the component.
4. Restart Home Assistant.

### Method 2: Manual Installation
1. Download this repository.
2. Copy the `custom_components/cambridge_cxa` directory into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration

This integration is configured entirely through the Home Assistant UI. **You no longer need to edit your `configuration.yaml` file.**

1. Go to **Settings > Devices & Services** in Home Assistant.
2. Click **+ Add Integration** in the bottom right corner.
3. Search for **Cambridge Audio CXA**.
4. Enter the required details:
   - **Host:** The IP address of your Raspberry Pi.
   - **Port:** The `ser2net` port (default is `5000`).
   - **Type:** Select `CXA61` or `CXA81` depending on your model.
   - **Name:** The name you want the Media Player entity to have.

Once added, a new Media Player entity will be created!

---

## Changelog
* **Performance Optimization:** Volume up and volume down commands (via the Raspberry Pi HTTP API) now utilize Home Assistant's centralized HTTP session pool (`async_get_clientsession`). This eliminates DNS and TCP handshake overhead on every button press, making volume adjustments near-instantaneous.
