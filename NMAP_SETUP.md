# Nmap Setup Documentation

## Installation

**Date:** 2026-07-13  
**Platform:** Windows (i686-pc-windows-windows)  
**Version:** Nmap 7.99

### Installation Path
```
C:\Program Files (x86)\Nmap\nmap.exe
```

### Verification
Command: `& "C:\Program Files (x86)\Nmap\nmap.exe" --version`

Output:
```
Nmap version 7.99 ( https://nmap.org )
Platform: i686-pc-windows-windows
Compiled with: nmap-liblua-5.4.8 openssl-3.0.16 nmap-libssh2-1.11.1 nmap-libz-1.3.2 nmap-libpcre2-10.47 Npcap-1.87 nmap-libdnet-1.18.0 ipv6
Compiled without:
Available nsock engines: iocp poll select
```

### System PATH
Added to system PATH via: `setx PATH "%PATH%;C:\Program Files (x86)\Nmap"`

## Usage

Full path (works immediately):
```powershell
& "C:\Program Files (x86)\Nmap\nmap.exe" [options] [target]
```

After new terminal session (once PATH is updated):
```powershell
nmap [options] [target]
```

## Next Steps (Day 3)
- Install python-nmap library
- Create Python wrapper for Nmap
- Write localhost scan script
