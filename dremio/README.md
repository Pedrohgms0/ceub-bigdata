# Camada Analítica na Arquitetura Data Lakehouse: Motor SQL e Virtualização de Dados

## 1. Introdução

O **Dremio** é um motor de consulta distribuído e plataforma de virtualização de dados projetado para fornecer acesso analítico unificado a múltiplas fontes, com desempenho comparável ao de Data Warehouses modernos. Sua arquitetura foi concebida para operar diretamente sobre **object stores** (como MinIO, Amazon S3 ou Azure Blob Storage) e formatos abertos (Parquet, ORC, Arrow), sem necessidade de movimentação ou duplicação de dados.

Na pilha moderna de **Data Lakehouse** utilizada neste curso, o Dremio representa o elo entre as camadas de processamento (Spark + Delta Lake) e a camada de consumo analítico (Metabase). Ele atua como um **motor SQL federado**, capaz de expor tabelas Delta como datasets consultáveis, consolidando a visão transacional e analítica do ambiente distribuído.

---

## 2. Fundamentação Teórica

Com o avanço das arquiteturas distribuídas e a convergência entre Data Lakes e Data Warehouses, emergiu a necessidade de motores SQL capazes de ler, transformar e unificar dados sem cópias redundantes. O Dremio insere-se nessa categoria de sistemas de **Data Lake Query Engine**, ao lado de tecnologias como **Trino**, **Presto** e **Athena**, oferecendo um modelo de processamento baseado em **Apache Arrow** e **Reflection Caching**, otimizando consultas sobre dados imutáveis e versionados.

Enquanto o **Apache Spark** se destaca no processamento de alto volume e transformação (ETL/ELT), o Dremio atua no **consumo interativo**, utilizando SQL padronizado e otimizando as consultas por meio de **reflections** — representações materializadas que aceleram a execução sem sacrificar a consistência com os dados originais. Essa combinação torna o Dremio ideal para compor a **camada Gold** da arquitetura Medallion, oferecendo acesso analítico sobre os dados governados pelo **Delta Lake**.

---

## 3. Arquitetura e Integração com o Lakehouse

A Figura 1 ilustra a posição do Dremio na pilha integrada Spark + MinIO + Delta + Metabase.

```mermaid
flowchart LR
    subgraph INGESTAO[Camada Bronze]
        A1[Fontes de Dados \n APIs / CSV / DBs]
        A2[MinIO (Object Store)]
    end

    subgraph PROCESSAMENTO[Camada Silver]
        B1[Apache Spark]
        B2[Delta Lake \n (Transações ACID e Versionamento)]
    end

    subgraph CONSUMO[Camada Gold]
        C1[Dremio \n (Motor SQL e Virtualização)]
        C2[Metabase \n (Visualização e BI)]
    end

    A1 --> A2 --> B1 --> B2 --> C1 --> C2

    style INGESTAO fill:#e7f0ff,stroke:#467fcf,stroke-width:1px
    style PROCESSAMENTO fill:#f4f4f4,stroke:#999,stroke-width:1px
    style CONSUMO fill:#fff7cc,stroke:#b29700,stroke-width:1px
```

**Figura 1.** Dremio como camada intermediária entre Delta Lake e Metabase na arquitetura Data Lakehouse.

O Dremio se conecta diretamente ao **MinIO** (camada de armazenamento) e reconhece automaticamente os arquivos Parquet e as tabelas Delta, permitindo consultas SQL sobre dados governados, sem a necessidade de pré-processamento. Em seguida, as visões e datasets criados no Dremio são expostos ao **Metabase** como fonte de dados analítica.

---

## 4. Integração Técnica

### 4.1. Conexão com o MinIO

O Dremio suporta object stores compatíveis com o protocolo S3. Para conectá-lo ao **MinIO**, é necessário registrar uma nova fonte com as seguintes configurações:

- **Nome da fonte**: `minio`
- **Tipo**: *Amazon S3*;
- **Endpoint**: `http://minio:9000`;
- **Access Key** e **Secret Key**: conforme configurado no ambiente;
- **Root Path**: `datalake/` (ou diretório padrão do bucket);
- **Enable compatibility mode**: `true` (necessário para compatibilidade com MinIO).

Após a configuração, o Dremio reconhecerá as tabelas Delta e Parquet armazenadas no bucket, permitindo consultas SQL diretas.

### 4.2. Conexão com o Metabase

O Metabase acessa o Dremio por meio de driver JDBC. Uma vez que o Dremio expõe datasets sob o catálogo lógico, é possível configurar o Metabase da seguinte forma:

- **Tipo de Banco**: Dremio;
- **Host**: `dremio:31010`;
- **Usuário**: credencial de leitura;
- **Database**: nome do espaço de trabalho ou schema;
- **Driver JDBC**: `dremio-jdbc-driver.jar`.

Assim, consultas SQL criadas no Metabase são traduzidas e executadas pelo Dremio sobre as tabelas Delta Lake, preservando a consistência transacional e aproveitando otimizações internas como o **Arrow Flight**.

### 4.3. Execução via Docker Compose

A seguir, um exemplo mínimo de implantação integrada com MinIO e Metabase.

```yaml
version: '3.9'
services:
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: admin123
    volumes:
      - ./minio-data:/data

  dremio:
    image: dremio/dremio-oss:latest
    ports:
      - "9047:9047"  # UI
      - "31010:31010" # JDBC
    volumes:
      - ./dremio-data:/opt/dremio/data
    depends_on:
      - minio

  metabase:
    image: metabase/metabase:latest
    ports:
      - "3000:3000"
    environment:
      MB_JETTY_PORT: 3000
    depends_on:
      - dremio
```

Após a inicialização, o acesso ao Dremio se dá via `http://localhost:9047` e ao Metabase via `http://localhost:3000`.

---

## 5. Funcionalidades Avançadas

### 5.1. Reflections e Caching

O Dremio permite criar *Reflections* — materializações otimizadas de consultas SQL — que reduzem a latência de leitura e eliminam recomputações desnecessárias. O sistema seleciona automaticamente o Reflection mais adequado para cada consulta, mantendo consistência com os dados originais.

### 5.2. Suporte a Delta Lake

Versões recentes do Dremio (>=24.x) incluem suporte nativo ao formato **Delta Lake**, permitindo leitura direta dos logs `_delta_log` e suporte a funcionalidades como *time travel* e *schema evolution*. Esse suporte o torna um componente essencial em ambientes **Lakehouse compatíveis com Spark**.

### 5.3. Segurança e Governança

O Dremio oferece controle de acesso granular (usuários, grupos, roles), autenticação LDAP/SAML, logging centralizado e auditoria de queries, atendendo aos requisitos de conformidade e rastreabilidade típicos de ambientes corporativos e acadêmicos.

---

## 6. Comparativo Técnico

| Motor SQL | Licenciamento | Formatos Suportados | Compatibilidade Lakehouse | Destaque |
|------------|----------------|---------------------|---------------------------|-----------|
| **Dremio** | Open Source / Enterprise | Parquet, Iceberg, Delta, ORC | Alta (Spark, MinIO, Delta) | Caching via Reflections e Arrow Flight |
| **Trino** | Apache 2.0 | Parquet, ORC, Avro | Alta (conectores extensíveis) | Escalabilidade e paralelismo massivo |
| **Athena** | Proprietário (AWS) | Parquet, ORC | Alta (S3) | Simplicidade e integração AWS |
| **PrestoDB** | Apache 2.0 | Parquet, ORC | Média | Consultas distribuídas interativas |

---

## 7. Prática com Hive e Dremio

Com o ambiente operacional ativo e o Hive Metastore integrado, é possível verificar o fluxo completo de interoperabilidade entre o Spark (camada de processamento) e o Dremio (camada de consulta e virtualização).

O objetivo desta etapa é demonstrar a unificação semântica dos metadados — isto é, a capacidade de ambos os motores interpretarem a mesma tabela Delta armazenada no MinIO, a partir das definições persistidas no Hive.

O primeiro passo consiste em criar e registrar uma tabela Delta no catálogo. Dentro do contêiner Spark, execute:

```bash
docker exec -it spark pyspark \
  --conf spark.sql.catalogImplementation=hive \
  --conf hive.metastore.uris=thrift://hive-metastore:9083
```

Em seguida, no ambiente PySpark interativo (Jupyter):

```python
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

spark = (
    SparkSession.builder
    .appName("HiveCatalogTest")
    .config("spark.sql.catalogImplementation", "hive")
    .config("hive.metastore.uris", "thrift://hive-metastore:9083")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .getOrCreate()
)

# Caminho da tabela no MinIO
path = "s3a://datalake/f1_2022_delta"

# Criação da tabela no catálogo Hive
spark.sql(f"""
CREATE TABLE f1_2022_delta
USING DELTA
LOCATION '{path}'
""")

spark.sql("SHOW TABLES").show()
```

Esse comando registra no Hive Metastore uma referência lógica (f1_2022_delta) associada à localização física da tabela no MinIO. A partir deste ponto, o catálogo Hive passa a descrever essa estrutura, permitindo que qualquer engine conectada (Spark, Dremio, Trino, Presto) acesse o mesmo conjunto de dados com consistência.

### Validação da Tabela via Spark SQL

Após o registro, a tabela pode ser consultada diretamente pelo Spark SQL — sem necessidade de apontar o caminho físico.

```sql
SELECT driver, constructor, SUM(points) AS total_points
FROM f1_2022_delta
GROUP BY driver, constructor
ORDER BY total_points DESC
LIMIT 10;
```

Caso o catálogo esteja funcionando corretamente, o Spark buscará automaticamente a definição no Hive Metastore (`thrift://hive-metastore:9083`) e executará a consulta sobre os dados no MinIO. Esse comportamento confirma que o catálogo foi persistido e está acessível de forma transacional.

### Verificação no Hive Metastore (CLI)

Também é possível inspecionar o catálogo diretamente pela CLI do Hive (caso instalada no contêiner):

```
docker exec -it hive-metastore bash
beeline -u jdbc:hive2://localhost:10000 -n hive
```

Dentro do prompt:

```bash
SHOW DATABASES;
USE default;
SHOW TABLES;
DESCRIBE FORMATTED f1_2022_delta;
```

A saída deve conter as colunas, o formato (DELTA), e a localização física ex: `s3a://datalake/f1_2022_delta`.

5.4. Descoberta Automática no Dremio

Ao acessar o Dremio em http://localhost:9047
:

Vá até Sources → Hive.

Verifique se o catálogo aparece conectado (thrift://hive-metastore:9083).

Expanda o banco default.

Localize e abra a tabela f1_2022_delta.

O Dremio reconhecerá automaticamente as colunas e tipos definidos no Hive Metastore e permitirá execução de consultas SQL diretas, como:

```bash
SELECT year, driver, SUM(points) AS total_points
FROM hive.default.f1_2022_delta
GROUP BY year, driver
ORDER BY total_points DESC;
```

Além disso, é possível:

- Criar reflections (mecanismos de cache distribuído);
- Integrar com o Metabase ou outras ferramentas de BI;
- Visualizar estatísticas e tipos inferidos automaticamente.

5.5. Consistência entre Engines

Esse fluxo comprova a integração horizontal de metadados, princípio central das arquiteturas Lakehouse:

| Etapa               | Componente       | Função                                                | Resultado                                           |
|---------------------|------------------|-------------------------------------------------------|-----------------------------------------------------|
| 1. Escrita          | Spark + Delta    | Criação da tabela Delta e gravação no MinIO.          | Gera `_delta_log` e arquivos Parquet.              |
| 2. Registro         | Hive Metastore   | Associação lógica entre nome e localização física.    | Cria metadado persistente em PostgreSQL.           |
| 3. Consulta Analítica | Dremio          | Leitura do catálogo Hive e execução SQL.              | Acesso consistente e compartilhado ao dataset.     |

>Essa interoperabilidade reflete o novo paradigma de governança distribuída: o Hive Metastore atua como repositório neutro e universal, integrando engines distintas e garantindo persistência e coerência dos metadados em toda a arquitetura. 

## 8. Conclusão

O Dremio consolida-se como um dos motores centrais das arquiteturas Data Lakehouse, atuando como uma camada SQL unificada sobre object stores e catálogos transacionais. Ele abstrai a complexidade do armazenamento distribuído e oferece uma interface analítica de alto desempenho capaz de federar múltiplas fontes — incluindo o MinIO, o Hive Metastore e o Delta Lake — em um modelo de dados lógico, consistente e governado. Ao integrar-se diretamente ao Spark, o Dremio passa a consumir as mesmas tabelas Delta registradas no Hive, preservando consistência semântica e eliminando a necessidade de pipelines redundantes de ingestão ou modelagem. Quando conectado ao Metabase, completa-se o ciclo analítico: o Spark executa as transformações e garante as propriedades ACID; o Hive registra e compartilha os metadados; o Dremio virtualiza e otimiza as consultas SQL; e o Metabase provê visualização e disseminação dos indicadores. Esse arranjo representa, na prática, a materialização do paradigma Lakehouse — uma arquitetura unificada que combina flexibilidade operacional, governança estruturada e consumo analítico ágil sobre dados distribuídos.

No contexto educacional e de pesquisa, o Dremio oferece um ambiente particularmente didático: permite compreender de forma concreta os conceitos de virtualização de dados, interoperabilidade multi-engine e governança distribuída, sem exigir infraestrutura complexa ou dependência de provedores comerciais. Em laboratório, reproduz fielmente o comportamento de plataformas corporativas de nível enterprise, tornando possível demonstrar a jornada completa do dado — da ingestão no MinIO, passando pelo processamento transacional no Spark e registro de metadados no Hive, até a consulta e visualização analítica via Dremio e Metabase. Essa implementação comprova que o Hive, longe de ser um vestígio histórico do Hadoop, mantém papel estrutural nas arquiteturas contemporâneas. Como catálogo de metadados universal, ele fornece uniformidade semântica, rastreabilidade e governança centralizada, unindo armazenamento físico (MinIO), processamento transacional (Spark + Delta) e virtualização analítica (Dremio) em um ecossistema coeso, interoperável e academicamente reprodutível. Essa persistência funcional transforma o Hive no elo conceitual e técnico entre a era do Hadoop e o paradigma moderno do Data Lakehouse.