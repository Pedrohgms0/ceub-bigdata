#!/bin/bash
set -e

echo "Aguardando PostgreSQL inicializar..."
until nc -z hive-postgres 5432; do
  sleep 2
done

echo "Inicializando schema do Hive Metastore..."
schematool -dbType postgres -initSchema
echo "Schema inicial criado com sucesso."
