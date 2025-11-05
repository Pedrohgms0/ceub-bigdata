# Dremio na Arquitetura Data Lakehouse: Motor SQL e Virtualização sobre Spark, MinIO e Delta Lake

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

## 7. Conclusão

O **Dremio** consolida-se como um dos motores centrais da arquitetura **Data Lakehouse**, oferecendo uma camada SQL unificada que integra armazenamento distribuído, governança transacional e consumo analítico. Sua integração com o **Spark**, o **Delta Lake** e o **Metabase** estabelece um pipeline completo, desde a ingestão até a visualização, com base em padrões abertos e sem dependência de fornecedores.

No contexto educacional e de pesquisa, o Dremio oferece uma plataforma robusta e transparente para o ensino de conceitos de **virtualização de dados, governança distribuída e processamento analítico sobre object stores**, permitindo que estudantes e profissionais experimentem arquiteturas de nível corporativo em ambientes de laboratório reprodutíveis.

