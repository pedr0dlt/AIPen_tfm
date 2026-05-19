#!/bin/bash
set -e

MSF_RPC_USER="${MSF_RPC_USER:-msf}"
MSF_RPC_PASS="${MSF_RPC_PASS:-msf123}"
MSF_RPC_PORT="${MSF_RPC_PORT:-55553}"

echo "[start.sh] Lanzando msfrpcd en :${MSF_RPC_PORT} (user=${MSF_RPC_USER})..."
msfrpcd -U "${MSF_RPC_USER}" -P "${MSF_RPC_PASS}" -a 0.0.0.0 -p "${MSF_RPC_PORT}" -S -f &
MSFRPCD_PID=$!
echo "[start.sh] msfrpcd PID=${MSFRPCD_PID} (carga inicial: 10-30s)"

echo "[start.sh] Lanzando uvicorn en :8000..."
exec uvicorn server:app --host 0.0.0.0 --port 8000
