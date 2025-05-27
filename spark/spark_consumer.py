# spark/spark_consumer.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import (StructType, StructField, StringType, 
                              DoubleType, IntegerType, TimestampType,
                              BooleanType, ArrayType)
import os
import logging
from pyspark.sql.streaming import StreamingQueryException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("RetailSparkConsumer")

# Environment Configuration
KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "kafka:9092")  # Default to Docker service name
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "retail-transactions")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")  # Docker service name
CHECKPOINT_LOCATION = os.getenv("CHECKPOINT_LOCATION", "/tmp/spark-checkpoints")

# Define schema for incoming JSON data (unchanged)
# Define schema for incoming JSON data
SCHEMA = StructType([
    StructField("transaction_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("store_id", IntegerType()),
    StructField("store_name", StringType()),
    StructField("store_location", StructType([
        StructField("city", StringType()),
        StructField("state", StringType()),
        StructField("region", StringType()),
        StructField("zip", StringType())
    ])),
    StructField("customer", StructType([
        StructField("id", StringType()),
        StructField("loyalty_member", BooleanType())
    ])),
    StructField("items", ArrayType(StructType([
        StructField("category", StringType()),
        StructField("price", DoubleType()),
        StructField("quantity", DoubleType())
    ]))),
    StructField("payment", StructType([
        StructField("method", StringType()),
        StructField("card_type", StringType())
    ])),
    StructField("summary", StructType([
        StructField("subtotal", DoubleType()),
        StructField("tax_rate", DoubleType()),
        StructField("tax_amount", DoubleType()),
        StructField("total", DoubleType())
    ])),
])


def create_spark_session():
    """Initialize Spark with Kafka/MongoDB packages"""
    return SparkSession.builder \
        .appName("RetailStreamProcessor") \
        .config("spark.jars.packages", 
               "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
               "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

def process_stream(spark):
    """Main stream processing logic"""
    try:
        # Read from Kafka with failover support
        df = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BROKERS) \
            .option("subscribe", KAFKA_TOPIC) \
            .option("failOnDataLoss", "false") \
            .option("startingOffsets", "earliest") \
            .load()

        # Parse JSON with schema validation
        transactions = df.select(
            from_json(col("value").cast("string"), SCHEMA).alias("data")
        ).select("data.*")

        # Write to MongoDB with optimized batching
        query = transactions.writeStream \
            .format("mongodb") \
            .option("uri", MONGO_URI) \
            .option("database", "retail_analytics") \
            .option("collection", "transactions") \
            .option("checkpointLocation", CHECKPOINT_LOCATION) \
            .outputMode("append") \
            .start()

        return query

    except StreamingQueryException as e:
        logger.error(f"Streaming query failed: {e}")
        raise

if __name__ == "__main__":
    spark = create_spark_session()
    logger.info("Spark session created with Kafka/MongoDB support")
    
    try:
        query = process_stream(spark)
        logger.info(f"Streaming query started: {query.id}")
        query.awaitTermination()
    except Exception as e:
        logger.critical(f"Application failed: {e}", exc_info=True)
        spark.stop()
        exit(1)