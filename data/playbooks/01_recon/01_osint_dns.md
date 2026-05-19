# RECON — OSINT y DNS

## Reconocimiento Pasivo
```bash
host <DOMAIN>
whois <DOMAIN>
curl http://<TARGET_IP>/robots.txt
curl http://<TARGET_IP>/sitemap.xml
whatweb http://<DOMAIN>
wafw00f <DOMAIN>
sublist3r -d <DOMAIN>
sublist3r -d <DOMAIN> -b
```

## DNS Activo
```bash
sudo nano /etc/hosts
# Añadir: <IP> <DOMAIN>

dnsrecon -d <DOMAIN>
dnsenum <DOMAIN>

dig <DOMAIN>
dig axfr @<NS_NAME> <DOMAIN>

fierce --domain <DOMAIN>
fierce --domain <DOMAIN> --subdomain-file /usr/share/dnsenum/dns.txt

httrack http://<TARGET>
```

## Subdominios con Wfuzz
```bash
wfuzz -c --hc=404 --hl=1 -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt -H "Host: FUZZ.<DOMAIN>" -u http://<TARGET_IP>
```

## Wordlists de referencia
| Tipo | Ruta |
|------|------|
| Usuarios | `/usr/share/metasploit-framework/data/wordlists/unix_users.txt` |
| Passwords | `/usr/share/wordlists/rockyou.txt` |
| Directorios | `/usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt` |
| DNS | `/usr/share/dnsenum/dns.txt` |
