# RECON — Host Discovery y Port Scanning

## Host Discovery
```bash
ping -c 1 <IP>
fping -a -g <IP>/<MASK>
arp-scan -I eth0 --localnet
netdiscover -i eth0 -r <IP_RED>/24
nmap -sn <IP_RED>/24
```
> TTL=128 → Windows | TTL=64 → Linux

## Port Scanning
```bash
# Rápido — todos los puertos TCP
sudo nmap -sS --min-rate 5000 -p- --open <TARGET_IP> -oN tcp_scan.txt

# Servicios y scripts sobre puertos encontrados
nmap -p<PORTS> -sC -sV -O <TARGET_IP> -Pn --open -oN full_scan.txt

# Completo y agresivo
sudo nmap -p- --open -sS -sC -sV --min-rate 2000 -n -Pn <TARGET_IP> -oN escaneo.txt

# UDP top 200
nmap -sU --top-ports 200 --min-rate=500 -Pn <TARGET_IP>

# Vulnerabilidades
nmap --script "vuln" -p<PORT> <TARGET_IP>

# Detección firewall
nmap -sA <TARGET_IP>
```

## Evasión IDS/FW
```bash
nmap -Pn -sS -sV -F -f <TARGET_IP>
nmap -Pn -sS -F -f --mtu 8 <TARGET_IP>
nmap -Pn -sSVC -p<PORTS> -f -D <DECOY_IP1>,<DECOY_IP2> <TARGET>
```
