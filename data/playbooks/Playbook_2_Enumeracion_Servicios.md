# 🔎 PLAYBOOK 2 — ENUMERACIÓN DE SERVICIOS

> **Objetivo:** Extraer información detallada de cada servicio descubierto en la fase de reconocimiento.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 03, 08 (Enumeración MSF), 10

---

## 2.1 — FTP (Puerto 21)

### Nmap Scripts
```bash
sudo nmap -p 21 -sV -sC -O <TARGET_IP>
nmap -p 21 --script ftp-anon <TARGET_IP>
nmap -p 21 --script ftp-brute --script-args userdb=<USERS_LIST> <TARGET_IP>
```

### Conexión manual
```bash
ftp <TARGET_IP>
# Anonymous login → Usuario: Anonymous / Contraseña: (vacía)

# Comandos FTP internos:
ls            # Listar
get /archivo  # Descargar
put /archivo  # Subir
pwd           # Directorio actual
exit          # Salir
```

### MSF — Enumeración FTP
```bash
use auxiliary/scanner/ftp/ftp_version
use auxiliary/scanner/ftp/ftp_login
use auxiliary/scanner/ftp/anonymous
```

---

## 2.2 — SSH (Puerto 22)

### Nmap Scripts
```bash
sudo nmap -p 22 -sV -sC -O <TARGET_IP>
nmap -p 22 --script ssh2-enum-algos <TARGET_IP>
nmap -p 22 --script ssh-hostkey --script-args ssh_hostkey=full <TARGET_IP>
nmap -p 22 --script ssh-auth-methods --script-args="ssh.user=<USER>" <TARGET_IP>
nmap -p 22 --script=ssh-brute --script-args userdb=<USERS_LIST> <TARGET_IP>
nmap -p 22 --script=ssh-run --script-args="ssh-run.cmd=cat /etc/passwd, ssh-run.username=<USER>, ssh-run.password=<PW>" <TARGET_IP>
```

### Conexión manual
```bash
ssh <USER>@<TARGET_IP>
ssh root@<TARGET_IP>
ssh <USER>@<TARGET_IP> -i /ruta/clave_privada
```

### MSF — Enumeración SSH
```bash
use auxiliary/scanner/ssh/ssh_version
use auxiliary/scanner/ssh/ssh_login
use auxiliary/scanner/ssh/ssh_enumusers
```

---

## 2.3 — SMTP (Puertos 25, 465, 586)

### Nmap Scripts
```bash
sudo nmap -p 25 -sV -sC -O <TARGET_IP>
nmap -sV -script banner <TARGET_IP>
```

### Conexión manual
```bash
nc <HOSTNAME>/<IP> <PUERTO>
telnet <HOSTNAME>/<IP> <PUERTO>

# Comandos SMTP internos:
VRFY <usuario>                                    # Verifica si existe
EHLO <nombre>                                     # Muestra capacidades
MAIL FROM:<email>                                 # Emisor
RCPT TO:<usuario>                                 # Receptor
DATA                                              # Cuerpo del mensaje
```

### MSF — Enumeración SMTP
```bash
use auxiliary/scanner/smtp/smtp_enum
use auxiliary/scanner/smtp/smtp_version
```

---

## 2.4 — HTTP/HTTPS (Puertos 80, 443)

### Herramientas manuales
```bash
whatweb <TARGET_IP>
browsh --startup-url http://<TARGET_IP>
wget <TARGET_IP>
curl <TARGET_IP> | more
curl -I http://<TARGET_IP>/<DIR>
curl --digest -u <USER>:<PW> http://<TARGET_IP>/<DIR>
lynx <TARGET_IP>
dirb http://<TARGET_IP>
dirb http://<TARGET_IP> /usr/share/metasploit-framework/data/wordlists/directory.txt
```

### MSF — Enumeración HTTP
```bash
use auxiliary/scanner/http/http_version
use auxiliary/scanner/http/http_header
use auxiliary/scanner/http/robots_txt
use auxiliary/scanner/http/dir_scanner
use auxiliary/scanner/http/dir_listing
use auxiliary/scanner/http/brute_dirs
use auxiliary/scanner/http/files_dir
use auxiliary/scanner/http/http_login
use auxiliary/scanner/http/http_put
use auxiliary/scanner/http/apache_userdir_enum
```

---

## 2.5 — SMB (Puertos 139, 445) — Windows

### Nmap Scripts
```bash
sudo nmap -p 445 -sV -sC -O <TARGET_IP>
nmap -p 445 --script smb-protocols <TARGET_IP>
nmap -p 445 --script smb-security-mode <TARGET_IP>
nmap -p 445 --script smb-os-discovery <TARGET_IP>
nmap -p 445 --script smb-enum-sessions <TARGET_IP>
nmap -p 445 --script smb-enum-shares <TARGET_IP>
nmap -p 445 --script smb-enum-shares --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-enum-users --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-enum-domains --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-enum-groups --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-enum-services --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-enum-shares,smb-ls --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmap -p 445 --script smb-server-stats --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmblookup -A <TARGET_IP>
```

### SMBClient
```bash
smbclient -L //<TARGET_IP> -N                    # Null session
smbclient -L //<TARGET_IP> -U '<USER>'           # Con credenciales
smbclient //<TARGET_IP>/<SHARE> -U '<USER>'      # Acceder a share
smbclient //<TARGET_IP>/public -N                # Share público
```

### SMBMap
```bash
smbmap -u guest -p "" -d . -H <TARGET_IP>
smbmap -u <USER> -p '<PW>' -d . -H <TARGET_IP>
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> -x 'ipconfig'       # Ejecutar comando
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> -L                   # Listar drives
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> -r 'C$'              # Listar contenido
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --upload '/root/backdoor' 'C$\backdoor'
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --download 'C$\flag.txt'
```

### CrackMapExec
```bash
crackmapexec smb <TARGET_IP> -u <USER> -p <PW>                 # Verificar creds
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> --users         # Enumerar usuarios
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> -x ipconfig     # Ejecutar comando
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> --sam            # Obtener hashes SAM
```

### RPCClient — Null Session
```bash
rpcclient -U "" -N <TARGET_IP>
# Comandos internos:
srvinfo          # Info del servidor
querydispinfo    # Usuarios válidos
enumdomusers     # Enumerar usuarios
enumdomgroups    # Enumerar grupos
lookupnames admin
```

### MSF — Enumeración SMB
```bash
use auxiliary/scanner/smb/smb_enumusers
use auxiliary/scanner/smb/smb_enumshares
use auxiliary/scanner/smb/smb_login
use auxiliary/scanner/smb/smb_version
```

---

## 2.6 — MySQL (Puerto 3306)

### Conexión manual
```bash
mysql -h <TARGET_IP> -u root
mysql -h <TARGET_IP> -u <USER>

# Comandos internos:
show databases;
use <DB_NAME>;
select * from <TABLE>;
select count(*) from <TABLE>;
select load_file("/etc/shadow");
```

### Nmap Scripts
```bash
sudo nmap -p 3306 -sV -O <TARGET_IP>
nmap -p 3306 --script=mysql-empty-password <TARGET_IP>
nmap -p 3306 --script=mysql-info <TARGET_IP>
nmap -p 3306 --script=mysql-users --script-args="mysqluser='<USER>',mysqlpass='<PW>'" <TARGET_IP>
nmap -p 3306 --script=mysql-databases --script-args="mysqluser='<USER>',mysqlpass='<PW>'" <TARGET_IP>
nmap -p 3306 --script=mysql-dump-hashes --script-args="username='<USER>',password='<PW>'" <TARGET_IP>
```

### Microsoft SQL (Puerto 1433)
```bash
nmap -sV -sC -p 1433 <TARGET_IP>
nmap -p 1433 --script ms-sql-info <TARGET_IP>
nmap -p 1433 --script ms-sql-empty-password <TARGET_IP>
nmap -p 1433 --script ms-sql-xp-cmdshell --script-args mssql.username=<USER>,mssql.password=<PW>,ms-sql-xp-cmdshell.cmd="ipconfig" <TARGET_IP>
```

### MSF — Enumeración MySQL
```bash
use auxiliary/admin/mysql/mysql_enum
use auxiliary/admin/mysql/mysql_sql
use auxiliary/scanner/mysql/mysql_login
use auxiliary/scanner/mysql/mysql_version
use auxiliary/scanner/mysql/mysql_hashdump
use auxiliary/scanner/mysql/mysql_schemadump
```

---

## 2.7 — RDP (Puerto 3389)

```bash
xfreerdp /u:<USER> /p:<PASSWORD> /v:<TARGET_IP>:<PORT>
```

---

## 2.8 — WinRM (Puerto 5985)

```bash
crackmapexec winrm <TARGET_IP> -u <USER> -p <PW>               # Comprobar creds
crackmapexec winrm <TARGET_IP> -u <USER> -p <PW> -x ipconfig   # Ejecutar comando
evil-winrm -u <USER> -p <PASSWORD> -i <TARGET_IP>               # Login interactivo
evil-winrm -u <USER> -H <NTLM_HASH> -i <TARGET_IP>             # Login con hash
```

---

## 2.9 — POP3 (Puertos 110, 995)

### Conexión
```bash
telnet <IP> 110                              # Texto plano
nc -nv <IP> 110                              # Netcat
openssl s_client -connect <IP>:995 -quiet    # SSL/TLS
```

### Comandos internos POP3
```bash
USER <username>     # Login
PASS <password>     # Contraseña
STAT                # Estado del buzón
LIST                # Listar correos
RETR <number>       # Leer correo
QUIT                # Cerrar sesión
```

### Nmap + MSF
```bash
nmap -sV -p 110,995 --script pop3-capabilities,pop3-ntlm-info <IP>

# MSF
use auxiliary/scanner/pop3/pop3_version
set RHOSTS <IP>
run
```

---

## 2.10 — SNMP (Puerto 161 UDP)

```bash
onesixtyone -c /usr/share/wordlists/rockyou.txt <TARGET_IP>
snmpwalk -v 2c -c <COMMUNITY_STRING> <TARGET_IP>
```

---

## 2.11 — Enum4Linux
```bash
/usr/share/enum4linux/enum4linux.pl -a <TARGET_IP> | tee enum4linux.log
```
