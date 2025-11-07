#!/bin/bash
#
# setup_dremio_dirs.sh
# Prepara estrutura e permissões para o container Dremio

# Cria a pasta se não existir
if [ ! -d "./dremio-data" ]; then
  mkdir -p "./dremio-data"
  echo "Diretório ./dremio-data criado."
fi

# Ajusta permissões para o usuário padrão do container Dremio (UID/GID 999)
sudo chown -R 999:999 ./dremio-data
sudo chmod -R 755 ./dremio-data

echo "Permissões ajustadas para UID:GID 999:999."
