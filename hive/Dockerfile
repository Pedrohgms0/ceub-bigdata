FROM apache/hive:3.1.3

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl netcat && \
    rm -rf /var/lib/apt/lists/*

# Copia configuração e script
COPY hive-config/hive-site.xml /opt/hive/conf/hive-site.xml
COPY scripts/init-db.sh /opt/hive/scripts/init-db.sh
RUN chmod +x /opt/hive/scripts/init-db.sh

# Baixa o driver JDBC
RUN curl -L -o /opt/hive/lib/postgresql-42.2.24.jar \
    https://jdbc.postgresql.org/download/postgresql-42.2.24.jar

USER hive
