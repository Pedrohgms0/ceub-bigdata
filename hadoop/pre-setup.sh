#!/bin/bash
# ===========================================================
# Inicialização do Hive Metastore + Postgres
# ===========================================================

# 1. Garante que as pastas de dados existam
for folder in hive-postgres-data; do
  if [ ! -d "$folder" ]; then
    mkdir -p "$folder"
  fi
done

# 2. Ajusta permissões (uid/gid 1000 padrão dos containers)
sudo chown -R 1000:1000 hive-postgres-data

# 3. Sobe os serviços Hive + Postgres
docker compose up -d

# 4. Mostra o status
docker ps | grep hive
