# ENUM — SMTP (25) y HTTP/HTTPS (80/443)

## SMTP — Puerto 25
```bash
sudo nmap -p 25 -sV -sC -O <TARGET_IP>
nmap -sV -script banner <TARGET_IP>

nc <HOSTNAME> 25
telnet <HOSTNAME> 25
# VRFY <usuario> | EHLO <nombre> | MAIL FROM:<email> | RCPT TO:<usuario>

use auxiliary/scanner/smtp/smtp_enum
use auxiliary/scanner/smtp/smtp_version
```

## HTTP/HTTPS — Puertos 80/443
```bash
whatweb <TARGET_IP>
wget <TARGET_IP>
curl <TARGET_IP> | more
curl -I http://<TARGET_IP>/<DIR>
curl --digest -u <USER>:<PW> http://<TARGET_IP>/<DIR>
dirb http://<TARGET_IP>
dirb http://<TARGET_IP> /usr/share/metasploit-framework/data/wordlists/directory.txt

# MSF
use auxiliary/scanner/http/http_version
use auxiliary/scanner/http/http_header
use auxiliary/scanner/http/robots_txt
use auxiliary/scanner/http/dir_scanner
use auxiliary/scanner/http/files_dir
use auxiliary/scanner/http/http_login
use auxiliary/scanner/http/apache_userdir_enum
```
