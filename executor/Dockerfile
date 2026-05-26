FROM kalilinux/kali-rolling

ENV DEBIAN_FRONTEND=noninteractive

# Suite estándar de pentesting que el agente referencia en los playbooks.
# Se instala una sola vez en build; en runtime el agente sólo consume.
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Base Python + escaneo + msf
    nmap \
    metasploit-framework \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    # Bruteforce / cracking
    hydra \
    john \
    # sshpass: ssh no-interactivo con contraseña — necesario para que el
    # agente acceda al target tras crackear creds, sin TTY interactivo.
    sshpass \
    # cliente ssh/scp/sftp — sshpass los envuelve, así que tienen que
    # estar disponibles en el PATH del contenedor.
    openssh-client \
    # Web enumeration / exploitation
    gobuster \
    dirb \
    nikto \
    whatweb \
    wpscan \
    sqlmap \
    # SMB
    smbclient \
    enum4linux \
    # Exploit DB CLI
    exploitdb \
    # Wordlists base (rockyou.txt.gz vive en /usr/share/wordlists/)
    wordlists \
    seclists \
    && rm -rf /var/lib/apt/lists/* \
    # rockyou viene comprimido — el playbook lo referencia descomprimido.
    && if [ -f /usr/share/wordlists/rockyou.txt.gz ]; then \
         gunzip /usr/share/wordlists/rockyou.txt.gz; \
       fi

WORKDIR /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/start.sh

EXPOSE 8000 55553

CMD ["/app/start.sh"]
