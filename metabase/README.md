# Metabase na Arquitetura Data Lakehouse: Integração com Spark, MinIO, Delta Lake e Dremio

## 1. Introdução

A camada de visualização e análise de dados ocupa papel estratégico dentro da arquitetura moderna de dados. No contexto do **Data Lakehouse**, o Business Intelligence (BI) atua sobre dados já consolidados, fornecendo recursos de exploração interativa, construção de dashboards e disseminação de indicadores de desempenho. Entre as ferramentas open source que atendem a esse propósito, destaca-se o **Metabase**, cuja simplicidade operacional e compatibilidade com diversos bancos de dados o tornam particularmente adequado a ambientes acadêmicos e corporativos.

Concebido como uma solução de **Business Intelligence self-service**, o Metabase permite que usuários não técnicos construam consultas e visualizações diretamente sobre dados estruturados e semiestruturados, mantendo compatibilidade com bancos relacionais (PostgreSQL, MySQL, MariaDB) e mecanismos analíticos distribuídos (Trino, Dremio, Spark SQL). No contexto da pilha moderna implementada neste curso, o Metabase representa a **camada Gold de consumo analítico**, atuando sobre dados governados e versionados via **Delta Lake** e disponibilizados por meio de motores SQL como o **Dremio**.

---

## 2. Fundamentação Teórica

A arquitetura Data Lakehouse surge como convergência entre os modelos de **Data Warehouse** (estruturado e governado) e **Data Lake** (flexível e escalável), incorporando controle transacional (ACID), versionamento e schema enforcement sobre **object stores**. Em termos práticos, ela permite que diferentes aplicações — analíticas ou operacionais — acessem os mesmos dados com consistência e auditabilidade. O modelo conceitual **Medallion Architecture**, proposto por *Michael Armbrust* (Databricks, 2019), define três camadas progressivas de maturação dos dados:

- **Bronze**: dados brutos, extraídos das fontes originais e preservados integralmente;
- **Silver**: dados refinados, padronizados e normalizados;
- **Gold**: dados agregados e analíticos, prontos para consumo em BI e Machine Learning.

O **Metabase** integra-se diretamente a essa terceira camada (Gold), conectando-se a mecanismos SQL distribuídos como o **Dremio** ou **Trino**, que, por sua vez, acessam tabelas Delta armazenadas em **object stores** compatíveis com S3, como o **MinIO**. Assim, o BI opera sobre um ambiente transacional e versionado, preservando a governança e a integridade garantidas pela camada Delta Lake.

---

## 3. Arquitetura de Integração

A Figura 1 apresenta a visão conceitual da integração entre os componentes principais da pilha adotada neste curso.

```mermaid
flowchart LR
    subgraph INGESTAO[Camada Bronze]
        A1[Fontes de Dados \n APIs / CSV / DBs]
        A2[MinIO (Object Store)]
    end

    subgraph PROCESSAMENTO[Camada Silver]
        B1[Apache Spark]
        B2[Delta Lake \n ACID / Versionamento / Schema Enforcement]
    end

    subgraph CONSUMO[Camada Gold]
        C1[Dremio / Trino \n (SQL Engine)]
        C2[Metabase \n (BI e Dashboards)]
    end

    A1 --> A2 --> B1 --> B2 --> C1 --> C2

    style INGESTAO fill:#e7f0ff,stroke:#467fcf,stroke-width:1px
    style PROCESSAMENTO fill:#f4f4f4,stroke:#999,stroke-width:1px
    style CONSUMO fill:#fff7cc,stroke:#b29700,stroke-width:1px
```

**Figura 1.** Integração do Metabase à arquitetura Data Lakehouse (Spark + MinIO + Delta + Dremio).

O fluxo parte da ingestão de dados brutos (Bronze), passa pela transformação e normalização com **Spark** e **Delta Lake** (Silver), e culmina na camada de consumo (Gold), onde o **Dremio** atua como gateway SQL e o **Metabase** como interface de visualização.

---

## 4. Integração Técnica

### 4.1. Conexão do Metabase ao Dremio

O Metabase comunica-se com o **Dremio** via conector JDBC. O Dremio expõe as tabelas Delta Lake por meio de seu catálogo interno, permitindo consultas SQL sobre os datasets armazenados no **MinIO**.

**Configuração no Metabase:**
- Tipo de banco: *Dremio* (ou *PostgreSQL* se estiver usando a camada virtual de exportação);
- Host: `dremio:31010` (ou IP do contêiner);
- Database: `datalake` (ou schema configurado);
- Usuário: credencial de leitura;
- Driver JDBC: `dremio-jdbc-driver.jar` (disponível no site oficial da Dremio).

Após configurar a conexão, o Metabase automaticamente descobre os esquemas e tabelas publicados no catálogo, permitindo criar perguntas (queries) e dashboards sobre as tabelas Delta.

### 4.2. Exemplo de Docker Compose (Standalone)

Abaixo está um exemplo mínimo de execução do Metabase em contêiner isolado, adequado para testes locais:

```yaml
version: '3.9'
services:
  metabase:
    image: metabase/metabase:latest
    container_name: metabase
    ports:
      - "3000:3000"
    environment:
      MB_DB_FILE: /metabase-data/metabase.db
      MB_JETTY_PORT: 3000
    volumes:
      - ./metabase-data:/metabase-data
    depends_on:
      - dremio

  dremio:
    image: dremio/dremio-oss:latest
    container_name: dremio
    ports:
      - "9047:9047"
      - "31010:31010"
    volumes:
      - ./dremio-data:/opt/dremio/data
```

Esse ambiente disponibiliza o Metabase em `http://localhost:3000` e o Dremio em `http://localhost:9047`. O Dremio é configurado para acessar o **MinIO** como fonte de dados, expondo as tabelas Delta para o Metabase.

---

## 5. Funcionalidades e Boas Práticas

### 5.1. Recursos Essenciais do Metabase
- Query Builder e suporte a SQL nativo;
- Dashboards dinâmicos e interativos;
- Parâmetros e filtros customizáveis;
- Integração com Slack e e-mail para notificações de métricas;
- Controle de acesso por grupos e coleções.

### 5.2. Recomendações de Uso
- Organizar dashboards por domínio analítico (Financeiro, Operacional, Técnico);
- Definir nomenclatura consistente para consultas e métricas;
- Utilizar catálogos transacionais (Hive Metastore ou Glue) para garantir consistência dos dados consultados;
- Monitorar performance de queries, especialmente em conexões com engines distribuídas.

---

## 6. Comparativo Técnico

| Ferramenta | Licenciamento | Integração com Lakehouse | Motor SQL suportado | Segurança e Governança |
|-------------|----------------|---------------------------|---------------------|--------------------------|
| **Metabase** | Open Source / Pro | Alta (via Dremio / Trino) | PostgreSQL, Dremio, SparkSQL | ACLs e permissões básicas |
| **Apache Superset** | Apache 2.0 | Alta | Trino, Hive, SparkSQL | Suporte a OAuth e LDAP |
| **Power BI** | Comercial | Média (via gateway) | SQL Server, PostgreSQL, Spark | Governança corporativa avançada |

O Metabase destaca-se pelo equilíbrio entre simplicidade e capacidade analítica, sendo ideal para ambientes educacionais e provas de conceito.

---

## 7. Conclusão

O **Metabase**, quando integrado à pilha **Spark + MinIO + Delta Lake + Dremio**, consolida-se como uma solução de **Business Intelligence de código aberto** plenamente compatível com o paradigma **Data Lakehouse**. Sua utilização na camada Gold permite transformar dados versionados e governados em relatórios interativos, acessíveis e auditáveis. Ao adotar essa integração, obtém-se um ecossistema completo — da ingestão bruta à visualização analítica — com independência de fornecedores e aderência a padrões abertos de dados distribuídos.

Essa combinação demonstra que é possível construir uma infraestrutura analítica moderna, escalável e didaticamente transparente, mantendo compatibilidade com os princípios de governança e reprodutibilidade científica exigidos em contextos acadêmicos e corporativos.

