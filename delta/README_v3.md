## 4. Prática com Delta Lake

### 4.1. Leitura dos arquivos CSV (Bronze)

```python
drivers = spark.read.option("header", True).csv("/home/jovyan/data/drivers.csv")
constructors = spark.read.option("header", True).csv("/home/jovyan/data/constructors.csv")
races = spark.read.option("header", True).csv("/home/jovyan/data/races.csv")
circuits = spark.read.option("header", True).csv("/home/jovyan/data/circuits.csv")
results = spark.read.option("header", True).csv("/home/jovyan/data/results.csv")

print(f"Drivers: {drivers.count()} | Results: {results.count()}")
```

### 4.2. Transformação e Integração (Silver)

```python
drivers.createOrReplaceTempView("drivers")
constructors.createOrReplaceTempView("constructors")
races.createOrReplaceTempView("races")
circuits.createOrReplaceTempView("circuits")
results.createOrReplaceTempView("results")

query = """
SELECT 
    ra.year,
    ra.name AS race_name,
    c.name AS circuit,
    d.forename || ' ' || d.surname AS driver,
    d.nationality AS driver_nationality,
    cs.name AS constructor,
    cs.nationality AS constructor_nationality,
    rs.position,
    rs.points
FROM results rs
JOIN races ra ON ra.raceId = rs.raceId
JOIN drivers d ON d.driverId = rs.driverId
JOIN constructors cs ON cs.constructorId = rs.constructorId
JOIN circuits c ON c.circuitId = ra.circuitId
WHERE ra.year = 2022
"""

df = spark.sql(query)
df.show(20, truncate=False)
```

### 4.2.1. Escrita no Delta Lake

```python
delta_path = "s3a://datalake-bronze/f1_2022_results_delta"
df.write.format("delta").mode("overwrite").save(delta_path)
print("Tabela Delta gravada com sucesso em s3a://datalake-bronze/f1_2022_results_delta")
```

### 4.2.2. Leitura e Validação

```python
from delta.tables import DeltaTable

tabela_delta = DeltaTable.forPath(spark, delta_path)
df_delta = tabela_delta.toDF()
df_delta.show(5, truncate=False)
print(f"Linhas totais: {df_delta.count()}")
tabela_delta.history().select("version", "timestamp", "operation").show(truncate=False)
```