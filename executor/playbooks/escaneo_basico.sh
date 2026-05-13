#!/bin/bash
TARGET=$1

if [ -z "$TARGET" ]; then
    echo "Error: Falta la IP objetivo."
    echo "Uso: ./escaneo_basico.sh <IP>"
    exit 1
fi

echo " Iniciando Reconocimiento Rápido"
echo " Objetivo: $TARGET"

nmap -sV -F -T4 $TARGET

echo " Escaneo Finalizado"
