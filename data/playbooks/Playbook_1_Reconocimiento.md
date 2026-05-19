# 🔍 PLAYBOOK 1 — RECONOCIMIENTO

> **Objetivo:** Recopilar toda la información posible sobre el objetivo antes de interactuar directamente.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 01, 02, 13

---

## FASE 1.1 — Reconocimiento Pasivo (OSINT)

### 1.1.1 Resolución DNS con `host`
```bash
host <DOMAIN>
```
> Si devuelve 2 IPs, probablemente está detrás de Cloudflare.

### 1.1.2 Whois
```bash
whois <DOMAIN>
```
> Info: nombre de dominio, registrar, nameservers, fechas, DNSSEC.

### 1.1.3 Robots.txt y Sitemap
```bash
curl http://<TARGET_IP>/robots.txt
curl http://<TARGET_IP>/sitemap.xml
```

### 1.1.4 Tecnologías web — WhatWeb / Wappalyzer
```bash
whatweb http://<DOMAIN>
```

### 1.1.5 Detección de WAF — Wafw00f
```bash
wafw00f -l                # Lista WAFs conocidos
wafw00f <DOMAIN>          # Detectar WAF
wafw00f -a <DOMAIN>       # Detección extendida
```

### 1.1.6 Subdominios — Sublist3r (OSINT)
```bash
sublist3r -d <DOMAIN>
sublist3r -d <DOMAIN> -b  # Con fuerza bruta
```

---

## FASE 1.2 — Reconocimiento Activo (DNS)

### 1.2.1 Virtual Hosting — /etc/hosts
```bash
sudo nano /etc/hosts
# Añadir: <IP> <DOMAIN>
```

### 1.2.2 DNS Recon
```bash
dnsrecon -d <DOMAIN>
dnsenum <DOMAIN>
```
> Wordlist DNS: `/usr/share/dnsenum/dns.txt`

### 1.2.3 Dig — Zone Transfer
```bash
dig <DOMAIN>
dig axfr @<NS_NAME> <DOMAIN>
```

### 1.2.4 Fierce
```bash
fierce --domain <DOMAIN>
fierce --domain <DOMAIN> --subdomain-file /usr/share/dnsenum/dns.txt
```

### 1.2.5 Clonar sitio web — HTTrack
```bash
httrack http://<TARGET>
```

---

## FASE 1.3 — Host Discovery

### 1.3.1 Ping / Fping
```bash
ping -c 1 <IP>               # Linux
fping -a -g <IP>/<MASK>       # Escaneo de red
```
> TTL=128 → Windows | TTL=64 → Linux

### 1.3.2 ARP-Scan
```bash
ifconfig
arp-scan -I eth0 --localnet
```

### 1.3.3 Netdiscover
```bash
netdiscover -i eth0 -r <IP_RED>/24
```

### 1.3.4 Nmap — Host Discovery
```bash
nmap -sn <IP_RED>/24
```

---

## FASE 1.4 — Port Scanning

### 1.4.1 Nmap — Escaneo completo
```bash
# Escaneo rápido de todos los puertos TCP
sudo nmap -sS --min-rate 5000 -p- --open <TARGET_IP> -oN tcp_scan.txt

# Escaneo de servicios y scripts sobre puertos encontrados
nmap -p<PORTS> -sC -sV <TARGET_IP> -Pn --open -oN full_scan.txt

# Escaneo agresivo completo
sudo nmap -p- --open -sS -sC -sV --min-rate 2000 -n -vvv -Pn <TARGET_IP> -oN escaneo.txt
```

### 1.4.2 Nmap — UDP
```bash
nmap -sU --top-ports 200 --min-rate=500 -Pn <TARGET_IP>
```

### 1.4.3 Nmap — Detección de vulnerabilidades
```bash
nmap --script "vuln" -p<PORT> <TARGET_IP>
```

### 1.4.4 Nmap — Detección de Firewall (ACK Scan)
```bash
nmap -sA <TARGET_IP>          # Detectar firewall
nmap -Pn -sA -F <TARGET_IP>  # Ver filtered/unfiltered
```

### 1.4.5 Nmap — Evasión de IDS/FW
```bash
nmap -Pn -sS -sV -F -f <TARGET_IP>                              # Fragmentación
nmap -Pn -sS -F -f --mtu 8 <TARGET_IP>                          # MTU personalizado
nmap -Pn -sSVC -p<PORTS> -f -D <DECOY_IP1>,<DECOY_IP2> <TARGET> # IP Spoofing
```

---

## FASE 1.5 — Web Recon / Directory Fuzzing

### 1.5.1 Curl
```bash
curl -I <TARGET_IP>
curl -X GET <TARGET_IP>
curl -X OPTIONS <TARGET_IP> -v
curl -X POST <TARGET_IP>/login.php -d "name=john&password=password" -v
```

### 1.5.2 Nikto
```bash
nikto -h http://<TARGET_IP> -o niktoscan.txt
nikto -h http://<TARGET_IP>:<PORT>/ -id <USER>:<PASS>
```

### 1.5.3 Dirb
```bash
dirb http://<TARGET_IP>
```

### 1.5.4 Gobuster
```bash
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirb/common.txt -b 403,404 -x .php,.xml,.txt -r
```

### 1.5.5 Wfuzz — Directorios
```bash
wfuzz -c --hc 404 -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt http://<TARGET_IP>/FUZZ
```

### 1.5.6 Dirsearch
```bash
dirsearch -u http://<TARGET_IP>/
dirsearch -u http://<TARGET_IP>/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt
```

### 1.5.7 Wfuzz — Subdominios
```bash
wfuzz -c --hc=404 --hl=1 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -H "Host: FUZZ.<DOMAIN>" -u http://<TARGET_IP>
```

---

## FASE 1.6 — Wordlists de referencia

| Tipo | Ruta |
|------|------|
| Usuarios | `/usr/share/metasploit-framework/data/wordlists/unix_users.txt` |
| Passwords | `/usr/share/wordlists/rockyou.txt` |
| Passwords | `/usr/share/metasploit-framework/data/wordlists/common_pass.txt` |
| Directorios | `/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt` |
| Directorios | `/usr/share/wordlists/dirb/common.txt` |
| DNS | `/usr/share/dnsenum/dns.txt` |
| Subdominios | `/usr/share/wordlists/SecLists/Discovery/DNS/subdomains-top1million-110000.txt` |
