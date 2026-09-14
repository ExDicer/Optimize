#!/bin/bash

# URL mentah berkas optimizerv1_compiled.py dari GitHub/Hosting
ONLINE_SCRIPT_URL="https://raw.githubusercontent.com/ExDicer/Optimize/main/optc.py"

echo -e "\e[1;36m[*] Memeriksa dependensi Python & Curl...\e[0m"

if ! command -v python3 > /dev/null 2>&1; then
    echo -e "\e[1;31m[!] Python3 tidak ditemukan. Menginstal...\e[0m"
    pkg update -y && pkg install python -y
fi

if ! command -v curl > /dev/null 2>&1; then
    pkg install curl -y
fi

echo -e "\e[1;32m[*] Mengunduh dan mengeksekusi Optimizer Engine dari cloud...\e[0m\n"
sleep 1

# Eksekusi langsung di RAM tanpa simpan berkas fisik
python3 -c "$(curl -fsSL $ONLINE_SCRIPT_URL)" "$@"
