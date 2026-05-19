# RECON — Web Recon y Directory Fuzzing

## Análisis inicial
```bash
curl -I <TARGET_IP>
curl -X GET <TARGET_IP>
curl -X OPTIONS <TARGET_IP> -v
nikto -h http://<TARGET_IP> -o niktoscan.txt
```

## Directory Fuzzing
```bash
dirb http://<TARGET_IP>

gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirb/common.txt -b 403,404 -x .php,.xml,.txt -r

wfuzz -c --hc 404 -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt http://<TARGET_IP>/FUZZ

dirsearch -u http://<TARGET_IP>/
dirsearch -u http://<TARGET_IP>/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/directory-list-lowercase-2.3-medium.txt
```
