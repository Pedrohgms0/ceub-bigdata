#!/bin/bash
set -e

echo ">>> Preparando ambiente do Hive Metastore..."
echo ">>> Derrubando e removendo qualquer resquício anterior..."
docker compose down -v || true

echo ">>> Limpando volumes locais..."
rm -rf ./hive-postgres-data
rm -rf /var/lib/docker/volumes/*hive* 2>/dev/null || true
mkdir -p ./hive-postgres-data
chown -R 70:70 ./hive-postgres-data

echo ">>> Criando diretórios auxiliares..."
mkdir -p hive-config scripts
chmod -R 755 hive-config scripts

echo ">>> Diretórios preparados:"
ls -ld ./hive-config ./hive-postgres-data ./scripts

echo ">>> Pronto para executar o post-setup.sh"
