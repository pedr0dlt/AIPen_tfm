# ENUM — FTP (21) y SSH (22)

## FTP — Puerto 21
```bash
sudo nmap -p 21 -sV -sC -O <TARGET_IP>
nmap -p 21 --script ftp-anon <TARGET_IP>
nmap -p 21 --script ftp-brute --script-args userdb=<USERS_LIST> <TARGET_IP>

# Conexión manual
ftp <TARGET_IP>
# Anonymous → Usuario: Anonymous / Contraseña: (vacía)
# ls | get /archivo | put /archivo | pwd | exit

# MSF
use auxiliary/scanner/ftp/ftp_version
use auxiliary/scanner/ftp/ftp_login
use auxiliary/scanner/ftp/anonymous
```

## SSH — Puerto 22
```bash
sudo nmap -p 22 -sV -sC -O <TARGET_IP>
nmap -p 22 --script ssh2-enum-algos <TARGET_IP>
nmap -p 22 --script ssh-auth-methods --script-args="ssh.user=<USER>" <TARGET_IP>
nmap -p 22 --script=ssh-brute --script-args userdb=<USERS_LIST> <TARGET_IP>

# Conexión
ssh <USER>@<TARGET_IP>
ssh root@<TARGET_IP>
ssh <USER>@<TARGET_IP> -i /ruta/clave_privada

# MSF
use auxiliary/scanner/ssh/ssh_version
use auxiliary/scanner/ssh/ssh_login
use auxiliary/scanner/ssh/ssh_enumusers
```
