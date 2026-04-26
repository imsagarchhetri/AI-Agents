---
title: WiFi Authentication Failed Fix
category: network
subcategory: wifi_connectivity
tags: [wifi, 802.1x, radius, reboot]
version: 2.1
---
## Steps to Resolve
1. Forget network on device
2. Clear credential cache (`certutil -delStore` or macOS Keychain)
3. Reconnect with corporate SSO
4. If persists, check MAC address in RADIUS deny list