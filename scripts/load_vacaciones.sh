set -e

TAR_PATH="${TAR_PATH:-data/targets/vacaciones.tar}"
IMAGE_NAME="vacaciones"

if [ -n "$(docker images -q $IMAGE_NAME 2>/dev/null)" ]; then
  echo "[+] Imagen '$IMAGE_NAME' ya cargada en Docker. Nada que hacer."
  exit 0
fi

if [ ! -f "$TAR_PATH" ]; then
  echo "[!] No se encuentra $TAR_PATH"
  echo "    Descarga el zip de Vacaciones desde Dockerlabs y deja el .tar en data/targets/"
  exit 1
fi

echo "[*] Cargando $TAR_PATH en Docker..."
docker load -i "$TAR_PATH"
echo "[+] Imagen '$IMAGE_NAME' lista."
echo "    Siguiente paso: COMPOSE_PROFILES=vacaciones docker compose up -d"
