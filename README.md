# ESP32 Deauthentication Tool
A powerful, cross-platform Python toolkit for Wi-Fi deauthentication testing using only an ESP32 board and a data cable. With a simple command-line interface and interactive menus, you can easily erase and flash your ESP32, scan for Wi-Fi networks, and launch a variety of wireless attacks—all from your terminal. The tool also provides seamless WiFi reconnection to the ESP32's ManagementAP WiFi network (**SSID:** `ManagementAP`, **password:** `mgmtadmin`) on Windows, Linux, and macOS.

> **⚠️ Legal Notice:**  
> Deauthentication attacks are illegal without explicit permission from the network owner. This tool is intended strictly for educational, research, and authorized penetration testing purposes. Use responsibly and only on networks you own or have written authorization to test. The authors disclaim all liability for misuse.

## ✨ Features

- **One-Command Flashing:**  
    Effortlessly erase and flash your ESP32 with the included firmware (`bootloader.bin`, `partition-table.bin`, `esp32-wifi-penetration-tool.bin`) using simple CLI commands.

- **Interactive Attack Console:**  
    Scan for nearby Wi-Fi networks, select targets, and launch attacks via an intuitive interactive menu.

- **Automated WiFi Reconnection:**  
    Automatically reconnect your computer to the ESP32's ManagementAP WiFi network (**password:** `mgmtadmin`) using native tools:  
    &nbsp;&nbsp;• Windows: `netsh`  
    &nbsp;&nbsp;• Linux: `nmcli`  
    &nbsp;&nbsp;• macOS: `networksetup`

- **Flexible Attack Modes:**  
    Supports multiple attack types, including deauthentication (DoS), handshake capture, and PMKID collection.

- **Cross-Platform Support:**  
    Works on Windows, Linux, and macOS—no manual driver or interface setup required.

- **Easy Installation:**  
    Install directly from PyPI with all dependencies and firmware included.

- **Educational & Research Focused:**  
    Designed for cybersecurity students, researchers, and professionals to learn about Wi-Fi security in a controlled environment.

---

## Installation

### Prerequisites
- Python 3.7 or newer
- ESP32 board (e.g., ESP32-WROOM-32)
- USB cable with data wires
- Windows 10/11, Linux (e.g., Ubuntu with `nmcli`), or macOS for WiFi operations
- `sudo` privileges for Linux/macOS WiFi reconnection
- Firmware files (included in the package)

### Create a Virtual Environment
To avoid dependency conflicts, create and activate a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install the Package
Install `esp32-deauth` via pip:

```bash
pip install esp32-deauth
```

## Usage

### 1. Erase Flash Memory
Erase the ESP32's flash memory to ensure a clean slate before flashing:

```bash
esp32-deauth erase --port COM3
```

- `--port`: Serial port (e.g., `COM3` on Windows, `/dev/ttyUSB0` on Linux/macOS).
- `--baud`: Baud rate (default: 115200).

**Example (Linux/macOS)**:
```bash
esp32-deauth erase --port /dev/ttyUSB0 --baud 115200
```

### 2. Flash Firmware
Flash the ESP32 with the included firmware files:

```bash
esp32-deauth flash --port COM3
```

- `--port`: Serial port.
- `--baud`: Baud rate (default: 115200).

**Example (Linux/macOS)**:
```bash
esp32-deauth flash --port /dev/ttyUSB0 --baud 115200
```

This command uses `esptool` to write:
- `bootloader.bin` at `0x1000`
- `partition-table.bin` at `0x8000`
- `esp32-wifi-penetration-tool.bin` at `0x10000`

### 3. Run Interactive Mode
Launch the interactive Wi-Fi attack tool to scan networks, select targets, and perform attacks:

```bash
sudo esp32-deauth run
```

- **Note**: `sudo` is required on Linux/macOS for WiFi reconnection (`nmcli` or `networksetup`).
- Connect to the ESP32's `ManagementAP` WiFi network before running.
- The interactive menu offers:
  1. Scan WiFi Networks
  2. Attack Single Network
  3. Attack Multiple Selected Networks
  4. Attack All Networks
  5. Exit

**Example Output**:
```
=== ESP32 WiFi Attack Tool ===
1. Scan WiFi Networks
2. Attack Single Network
3. Attack Multiple Selected Networks
4. Attack All Networks
5. Exit
Select option:
```

### 4. Scan Wi-Fi Networks
Scan for available Wi-Fi networks and display their details (SSID, BSSID, RSSI):

```bash
sudo esp32-deauth scan
```

**Example Output**:
```
+----+----------+-------------------+-------+
| ID | SSID     | BSSID             | RSSI  |
+----+----------+-------------------+-------+
| 0  | Network1 | 00:11:22:33:44:55 | -50   |
| 1  | Network2 | 66:77:88:99:AA:BB | -60   |
+----+----------+-------------------+-------+
```

### 5. Run a Targeted Attack
Perform a deauthentication attack on a specific access point:

```bash
sudo esp32-deauth attack --ap-id 0 --attack-type DOS --attack-method DEAUTH_BROADCAST --timeout 225 --continuous
```

- `--ap-id`: ID of the target AP (from `scan` output).
- `--attack-type`: Attack type (`PASSIVE`, `HANDSHAKE`, `PMKID`, `DOS`; default: `DOS`).
- `--attack-method`: Method (e.g., `DEAUTH_BROADCAST`, `DEAUTH_ROGUE_AP`; default: `DEAUTH_BROADCAST`).
- `--timeout`: Attack duration in seconds (default: 225).
- `--continuous`: Run attack in a continuous loop (optional).

**Example**:
Attack AP with ID 0 in continuous DOS mode:
```bash
sudo esp32-deauth attack --ap-id 0 --attack-type DOS --attack-method DEAUTH_BROADCAST --timeout 225 --continuous
```

### Troubleshooting
- **Port Not Found**: Ensure the ESP32 is connected and the port is correct (e.g., `ls /dev/tty*` on Linux/macOS, Device Manager on Windows).
- **WiFi Reconnection Fails**:
  - Windows: Ensure `netsh` can see `ManagementAP` (`netsh wlan show networks`).
  - Linux: Verify `nmcli` is installed (`sudo apt install network-manager`) and the WiFi interface is detected.
  - macOS: Ensure `sudo` is used and `networksetup` can access the WiFi interface.
- **Server Unreachable**: Confirm the ESP32 is flashed with the correct firmware and connected to `ManagementAP`.
- **Permission Errors**: Use `sudo` for Linux/macOS commands requiring WiFi or serial port access.

## Development

### Project Structure
```
esp32-deauth/
├── esp32_deauth/
│   ├── __init__.py
│   ├── cli.py
│   ├── deauth.py
│   ├── firmware/
│   │   ├── esp32-wifi-penetration-tool.bin
│   │   ├── partition-table.bin
│   │   ├── bootloader.bin
├── README.md
├── setup.py
├── LICENSE
```

### Local Development
1. Clone or download the repository:
   ```bash
   git clone https://github.com/Ishanoshada/Esp32-Deauth.git
   cd Esp32-Deauth
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install the package locally:
   ```bash
   pip install -e .
   ```
5. Run tests:
   ```bash
   python -m unittest discover tests
   ```

### Contributing
Contributions are welcome! Please:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add your feature"`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

Contact: ishan.kodithuwakku.officals@gmail.com

## License
GNU General Public License v2.0 (see `LICENSE` file).


## Acknowledgments
- Inspired by the need for educational tools in cybersecurity research.
- Firmware is based on [esp32-wifi-penetration-tool](https://github.com/risinek/esp32-wifi-penetration-tool) by risinek.
- Thanks to the Python, `esptool`, and Flask communities for their excellent libraries.
- Built with contributions from the open-source community.

