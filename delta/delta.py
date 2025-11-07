#pip install delta-spark==3.2.1

import os
from pyspark.sql import SparkSession, Row
from delta.tables import DeltaTable
import importlib.metadata

print("Versão delta-spark (Python):", importlib.metadata.version("delta-spark"))

os.environ["SPARK_HOME"] = "/usr/local/spark"
os.environ["PYSPARK_SUBMIT_ARGS"] = (
    "--jars /usr/local/spark/jars/delta-spark_2.12-3.2.1.jar,"
    "/usr/local/spark/jars/delta-storage-3.2.1.jar pyspark-shell"
)

spark = (
    SparkSession.builder
    .appName("Delta-Bronze")
    .master("local[*]")
    .config("spark.executor.memory", "1g")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "true")
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000")
    .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

spark._jsc.hadoopConfiguration().set("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
print("Handler S3A inicializado com sucesso:", fs)

spark.sql("SELECT version()").show()

drivers = spark.read.option("header", True).csv("/home/jovyan/data/drivers.csv")
constructors = spark.read.option("header", True).csv("/home/jovyan/data/constructors.csv")
races = spark.read.option("header", True).csv("/home/jovyan/data/races.csv")
circuits = spark.read.option("header", True).csv("/home/jovyan/data/circuits.csv")
results = spark.read.option("header", True).csv("/home/jovyan/data/results.csv")

print(f"Drivers: {drivers.count()} | Results: {results.count()}")

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

!/usr/local/bin/mc alias set local http://minio:9000 minioadmin minioadmin
!mc --version
!mc mb --ignore-existing local/datalake-bronze
!mc mb --ignore-existing local/datalake-silver
!mc mb --ignore-existing local/datalake-gold
!mc mb --ignore-existing local/datalake-meta
!mc ls local

delta_path = "s3a://datalake-bronze/f1_2022_results_delta"

df.write.format("delta").mode("overwrite").save(delta_path)
print(f"Tabela Delta gravada com sucesso em {delta_path}")

tabela = DeltaTable.forPath(spark, delta_path)
df_read = tabela.toDF()
print("Total de registros lidos do Delta:", df_read.count())
df_read.show(10, truncate=False)
!mc ls local/datalake-bronze/f1_2022_results_delta/

delta_path = "s3a://datalake-bronze/f1_2022_results_delta"

spark.sql(f"""
UPDATE delta.`{delta_path}`
SET points = points + 1
WHERE driver = 'Lewis Hamilton'
""")

spark.sql(f"""
DELETE FROM delta.`{delta_path}`
WHERE position IS NULL
""")

updates = spark.createDataFrame([
    Row(year=2022, race_name="Brazil Grand Prix", driver="Lewis Hamilton", points=25),
    Row(year=2022, race_name="New Race", driver="New Driver", points=10)
])

updates.createOrReplaceTempView("updates")

spark.sql(f"""
MERGE INTO delta.`{delta_path}` AS target
USING updates AS source
ON target.driver = source.driver AND target.race_name = source.race_name
WHEN MATCHED THEN UPDATE SET target.points = source.points
WHEN NOT MATCHED THEN INSERT (year, race_name, driver, points)
VALUES (source.year, source.race_name, source.driver, source.points)
""")

tabela_delta = DeltaTable.forPath(spark, delta_path)
tabela_delta.history().select("version", "timestamp", "operation").show(truncate=False)

old_df = spark.read.format("delta").option("versionAsOf", 0).load(delta_path)
print("Versão inicial:")
old_df.show(5, truncate=False)

new_df = spark.read.format("delta").load(delta_path)
print("Versão atual:")
new_df.show(5, truncate=False)
