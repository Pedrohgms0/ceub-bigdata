#!/bin/bash
set -e

echo ">>> Subindo containers em modo passivo..."
docker compose up -d
sleep 10

echo ">>> Inicializando schema do Hive manualmente..."
docker compose exec hive-metastore bash -c "
  echo 'Aguardando PostgreSQL...';
  until nc -z hive-postgres 5432; do sleep 2; done;
  echo 'Conectando e inicializando schema...';
  /opt/hive/bin/schematool -dbType postgres -initSchema --verbose;
"

echo ">>> Schema criado com sucesso. Reiniciando container Hive..."
docker compose down
docker compose up -d

echo ">>> Setup completo."
docker compose ps
