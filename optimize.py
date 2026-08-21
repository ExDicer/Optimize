import os
import sys
import subprocess
import hashlib
import time
import re

# ==========================================
# 1. AUTO DEPENDENCY INSTALLER & LOGGING
# ==========================================
LOG_FILE = "feedback.txt"

def log_error(error_msg):
    with open(LOG_FILE, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] ERROR: {error_msg}\n")

def setup_environment():
    """Menginstal library ringan yang dibutuhkan secara otomatis"""
    try:
        subprocess.run(["command", "-v", "adb"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("[*] Menginstal android-tools (ADB)...")
        os.system("pkg update -y && pkg install android-tools -y")

    try:
        import rich
    except ImportError:
        print("[*] Menginstal library UI 'rich'...")
        subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)

setup_environment()

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.progress import track

console = Console()

# ==========================================
# 2. HARDWARE & POCO X3 PRO DETECTION MATRIX
# ==========================================
SUPPORTED_MODELS = [
    "Poco X3 Pro", "iQOO Z10 5G", "Poco M6 Pro", "Samsung Galaxy A10",
    "Vivo V50 Lite 4G", "Samsung A71 5G", "Poco C75", "Redmi 9T"
]

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception as e:
        log_error(f"Command failed '{cmd}': {str(e)}")
        return ""

def get_device_info():
    model = run_cmd("getprop ro.product.model")
    brand = run_cmd("getprop ro.product.brand")
    device_id = run_cmd("getprop ro.serialno") or run_cmd("getprop ro.build.id")
    
    if not model:
        model = run_cmd("getprop ro.product.marketname") or "Generic Android"
    
    full_name = f"{brand.capitalize()} {model}".strip()
    
    android_ver = run_cmd("getprop ro.build.version.release") or "12"
    try:
        sdk_ver = int(run_cmd("getprop ro.build.version.sdk") or 31)
    except ValueError:
        sdk_ver = 31

    miui_ver = run_cmd("getprop ro.miui.ui.version.name") or "V130"
    hyperos_ver = run_cmd("getprop ro.mi.os.version.name")
    
    oem_skin = "MIUI" if not hyperos_ver else "HyperOS"
    oem_version = miui_ver if not hyperos_ver else hyperos_ver

    detected_target = "Universal Android"
    for target in SUPPORTED_MODELS:
        if target.lower() in full_name.lower() or target.lower() in model.lower():
            detected_target = target
            break

    return {
        "model": model,
        "brand": brand.upper(),
        "full_name": full_name,
        "android_ver": android_ver,
        "sdk_ver": sdk_ver,
        "oem_skin": oem_skin,
        "oem_version": oem_version,
        "target_match": detected_target,
        "id": hashlib.md5(f"{model}{device_id}".encode()).hexdigest()[:8].upper()
    }

# ==========================================
# 3. DYNAMIC PASSWORD GENERATOR
# ==========================================
def generate_device_password(device_info):
    raw_key = f"{device_info['brand']}-{device_info['model']}-KEY2026"
    return hashlib.sha256(raw_key.encode()).hexdigest()[:8].upper()

def authenticate_user(device_info):
    valid_password = generate_device_password(device_info)
    console.print(Panel(f"[bold yellow]SECURITY LOCK[/bold yellow]\nPassword khusus ([cyan]{device_info['full_name']}[/cyan]): [bold green]{valid_password}[/bold green]", title="Autentikasi Perangkat"))
    
    attempts = 3
    while attempts > 0:
        user_input = Prompt.ask("[bold white]Masukkan Password Perangkat[/bold white]")
        if user_input.strip() == valid_password:
            console.print("[bold green]✓ Akses Diterima![/bold green]\n")
            return True
        else:
            attempts -= 1
            console.print(f"[bold red]✕ Password Salah![/bold red] Sisa percobaan: {attempts}")
    
    log_error("Akses ditolak.")
    sys.exit()

# ==========================================
# 4. DUAL ADB ROUTE SYSTEM
# ==========================================
class ADBManager:
    def __init__(self):
        self.mode = None
        
    def select_route(self):
        table = Table(title="Pilih Jalur Izin ADB")
        table.add_column("No", style="cyan", justify="center")
        table.add_column("Jalur Izin", style="bold green")
        table.add_row("1", "Shizuku (Wireless / rish)")
        table.add_row("2", "USB ADB Standar")
        console.print(table)
        
        choice = Prompt.ask("Pilih metode (1/2)", choices=["1", "2"])
        self.mode = "shizuku" if choice == "1" else "usb"

    def execute_shell(self, command):
        full_cmd = f"rish -c \"{command}\"" if self.mode == "shizuku" else f"adb shell \"{command}\""
        try:
            res = subprocess.run(full_cmd, shell=True, capture_output=True, text=True, timeout=15)
            if res.returncode != 0 and res.stderr:
                log_error(f"ADB Error: {res.stderr.strip()}")
            return res.stdout.strip()
        except Exception as e:
            log_error(f"ADB Exception: {str(e)}")
            return ""

# ==========================================
# 5. POCO X3 PRO SPECIFIC TUNERS
# ==========================================
def optimize_poco_x3_pro(adb_mgr, device_info):
    """Optimasi khusus Snapdragon 860 & MIUI 13 (Android 12)"""
    console.print(Panel("[bold green]Tuning Spesifik POCO X3 Pro (MIUI 13 / Android 12)[/bold green]"))
    
    tasks = [
        # Bypass PPK Android 12
        ("Fix Signal 9 / Anti Re-sync Play Services", "/system/bin/device_config set_sync_disabled_for_tests persistent"),
        ("Set Max Phantom Processes", "/system/bin/device_config put activity_manager max_phantom_processes 2147483647"),
        ("Disable Phantom Process Monitor", "settings put global settings_enable_monitor_phantom_procs false"),
        
        # Kill Aggressive Throttling Services
        ("Disable Joyose Thermal Limiter", "am force-stop com.xiaomi.joyose"),
        ("Disable MIUI Powerkeeper Throttling", "am force-stop com.miui.powerkeeper"),
        ("Disable System Ads Service (msa)", "am force-stop com.miui.msa.global"),
        
        # Lock 120Hz Refresh Rate (Anti Drop Hz)
        ("Lock Peak Refresh Rate 120Hz", "settings put system peak_refresh_rate 120.0"),
        ("Lock Min Refresh Rate 120Hz", "settings put system min_refresh_rate 120.0"),
        
        # Touch & Display Responsiveness
        ("Cut Window Animation (0.5x)", "settings put global window_animation_scale 0.5"),
        ("Cut Transition Animation (0.5x)", "settings put global transition_animation_scale 0.5"),
        ("Cut Animator Duration (0.5x)", "settings put global animator_duration_scale 0.5"),
        
        # Game Driver & Memory Tuning
        ("Direct Game Driver Integration", "settings put global game_driver_opt_in_apps com.tencent.ig,com.miHoYo.GenshinImpact"),
        ("Whitelist Game Doze Mode", "dumpsys deviceidle whitelist +com.tencent.ig"),
        ("Trim Caches", "pm trim-caches 999999999999"),
        ("Speed-Profile Compilation", "cmd package compile -m speed-profile -a")
    ]
    
    for desc, cmd in track(tasks, description="[cyan]Menerapkan parameter POCO X3 Pro..."):
        adb_mgr.execute_shell(cmd)
        time.sleep(0.3)
        
    console.print("[bold green]✓ Optimasi Spesifik POCO X3 Pro Selesai![/bold green]\n")

def optimize_pubg_network(adb_mgr):
    console.print(Panel("[bold yellow]Tuning Jitter Network PUBG Mobile[/bold yellow]"))
    net_tweaks = [
        "setprop net.tcp.buffersize.wifi 524288,1048576,2097152,262144,524288,1048576",
        "setprop net.tcp.buffersize.lte 524288,1048576,2097152,262144,524288,1048576",
        "setprop net.rmnet0.dns1 1.1.1.1",
        "setprop net.rmnet0.dns2 1.0.0.1",
        "setprop net.dns1 1.1.1.1",
        "ndc resolver setnetdns 100 local 1.1.1.1 1.0.0.1"
    ]
    for tweak in track(net_tweaks, description="[yellow]Melakukan Tuning Network..."):
        adb_mgr.execute_shell(tweak)
        time.sleep(0.2)
    console.print("[bold green]✓ Network Socket Berhasil Dioptimalkan![/bold green]\n")

# ==========================================
# MAIN EXECUTION FLOW
# ==========================================
def main():
    os.system("clear")
    console.print(Panel.fit("[bold blue]POCO X3 PRO PERFORMANCE TUNER[/bold blue]\n[dim]Snapdragon 860 & MIUI 13 Specialized Engine[/dim]", style="blue"))
    
    device_info = get_device_info()
    
    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(f"[bold]Device ID:[/bold] {device_info['id']}")
    grid.add_row(f"[bold]Perangkat:[/bold] {device_info['full_name']}")
    grid.add_row(f"[bold]OS Target:[/bold] {device_info['oem_skin']} {device_info['oem_version']} (Android {device_info['android_ver']})")
    console.print(Panel(grid, title="Informasi Perangkat"))

    authenticate_user(device_info)
    
    adb_mgr = ADBManager()
    adb_mgr.select_route()
    
    while True:
        console.print("\n[bold white]MENU OPTIMASI POCO X3 PRO:[/bold white]")
        console.print("1. Jalankan Total Optimasi Hardware & MIUI 13 (All-in-One)")
        console.print("2. Jalankan Tuning Network PUBG Mobile saja")
        console.print("3. Keluar")
        
        opt = Prompt.ask("Pilih tindakan", choices=["1", "2", "3"])
        
        if opt == "1":
            optimize_poco_x3_pro(adb_mgr, device_info)
            optimize_pubg_network(adb_mgr)
        elif opt == "2":
            optimize_pubg_network(adb_mgr)
        elif opt == "3":
            console.print("\n[bold blue]Selesai. Selamat Bermain![/bold blue]")
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
