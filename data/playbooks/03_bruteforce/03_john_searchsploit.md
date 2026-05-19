# BRUTEFORCE — John the Ripper y Searchsploit

## John the Ripper
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt <HASH_FILE>
hashid <HASH>
john --format=<FORMAT> --wordlist=/usr/share/wordlists/rockyou.txt <HASH_FILE>
john --format=NT hashes.txt

zip2john archivo.zip > hash && john --wordlist=/usr/share/wordlists/rockyou.txt hash
keepass2john archivo.kdbx > hash && john --wordlist=/usr/share/wordlists/rockyou.txt hash
ssh2john id_rsa > hashes.txt && john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

## Searchsploit
```bash
searchsploit <TERM>
searchsploit -m <EXPLOIT_ID>
searchsploit -t vsftpd
searchsploit -e "Windows 7"
searchsploit remote windows smb
searchsploit -w remote windows smb | grep -e "EternalBlue"
```

## Cross-Compiling
```bash
x86_64-w64-mingw32-gcc exploit.c -o exploit64.exe
i686-w64-mingw32-gcc exploit.c -o exploit32.exe
gcc -pthread exploit.c -o exploit -lcrypt
```
