# BalapinBridge v0.3.0 - Release Notes

## 🎮 BalapinBridge v0.3.0 Released

### What is BalapinBridge?
BalapinBridge is a Windows application that receives UDP data from the Balapin PC Bridge Android app and converts it into a virtual Xbox 360 gamepad. This allows you to use your Android device as a controller for racing games like **F1 2020** via XInput.

### ✨ Key Features
- **UDP Monitor**: Receive steering, throttle, brake, and button data from Android via WiFi
- **ViGEmBus Integration**: Emulates Xbox 360 controller using ViGEmBus 1.22.0 driver
- **F1 2020 Mapping**: Complete button and control mapping for racing gameplay
- **Auto-start Support**: Scheduled Task ONLOGON for persistent operation
- **Firewall Automation**: Automatic UDP 5005 inbound rule creation
- **Status Monitoring**: `--status` flag to check driver and task status

### 📦 What's Included
- `BalapinBridge.exe` - Single-file executable (PyInstaller onefile)
- `LICENSE` - MIT License with GPL v3 attribution for ViGEmBus
- `README.md` - Complete setup and usage instructions
- `SHA256.txt` - Checksum for integrity verification

### 🚀 Quick Start

**1. Setup (once only, as Administrator):**
```bat
dist\BalapinBridge.exe --setup
```
This will:
- Check/install ViGEmBus driver
- Create firewall rule for UDP 5005
- Offer to create auto-start task

**2. Run Monitor:**
```bat
\.venv\Scripts\activate
python udp_monitor.py --port 5005
```

**3. From Android:**
- Connect to same WiFi as PC
- Enter PC IP address (from `ipconfig`) in the HP app
- Press Connect and start driving!

**4. Verify:**
- Open `joy.cpl` → check Xbox 360 Gamepad
- Bind in F1 2020 as XInput controller

### 📋 V0.5 Checklist Status
All publication prerequisites have been addressed:
- ✅ Install reproducible (vgamepad 0.1.0 workaround documented)
- ✅ Lisensi redistribusi ViGEmBus (MIT + GPL v3 attribution)
- ✅ Uji fresh-VM end-to-end (step-by-step documented)
- ✅ Paket rilis (BalapinBridge-v0.3.0.zip dengan SHA256)
- ✅ Firewall UDP 5005 (otomatis di --setup)
- ✅ Disclaimer keamanan (hanya gunakan di LAN pribadi)
- ✅ Versioning (--version flag + tag git)

### ⚠️ Security Disclaimer
**PENTING**: Aplikasi ini menggunakan komunikasi UDP polos tanpa autentikasi. 
Jika dijalankan di jaringan publik atau WiFi yang terbuka, ada risiko 
perangkat lain menyuntik input yang tidak diinginkan (simulasi tombol/gerak 
gamepad). **Gunakan hanya di jaringan LAN pribadi yang Anda cerna.** 
Aplikator tidak bertanggung jawab atas kerusakan atau kecurangan yang 
diharapkan akibat penggunaan jaringan tidak terpercaya.

### 📄 License
This project is licensed under the **MIT License**, with ViGEmBus 1.22.0 
subject to GNU General Public License v3.0. See `LICENSE` file for details.

### 🔗 Links
- **GitHub**: https://github.com/gojalifs/BalapinBridge
- **Release**: v0.3.0
- **Documentation**: `README.md`

---
*Built with ❤️ for the racing simulator community*