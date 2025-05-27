
# kafka/producer.py
# Simulated Kafka Producer
print('Producing to Kafka...')

from kafka import KafkaProducer
import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KafkaProducer")
# Set up logger for the producer
def setup_logger(name):
    """Set up a logger with a specific name."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

logger = setup_logger("producer")

logger.info("Producer starting...")
# Initialize Kafka producer with retry configuration

max_retries = 5
retry_delay = 5

for attempt in range(max_retries):
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda x: x.encode('utf-8')
        )
        break
    except Exception as e:
        if attempt == max_retries - 1:
            raise
        time.sleep(retry_delay)

producer = None
while not producer:
    try:
        producer = KafkaProducer(
            bootstrap_servers=['kafka:29092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,
            retry_backoff_ms=1000
        )
        logger.info("Successfully connected to Kafka")
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e}")
        time.sleep(5)

# Kafka topic
topic = 'retail-stream'

# Stream source
uri = 'https://retails-api.amdari.io/stream'

while True:
    try:
        # Stream API with chunked response
        with requests.get(uri, stream=True) as response:
            if response.status_code == 200:
                logger.info("Connected to API stream.")
                for line in response.iter_lines():
                    if line:
                        try:
                            json_obj = json.loads(line.decode('utf-8'))
                            future = producer.send(topic, value=json_obj)
                            future.get(timeout=60)  # Wait for message to be delivered
                            logger.info(f"Sent to Kafka: {json_obj}")
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipped invalid JSON: {e}")
                        except Exception as e:
                            logger.error(f"Error sending message: {e}")
            else:
                logger.error(f"Failed to connect: {response.status_code}")
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
    except KeyboardInterrupt:
        break
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    time.sleep(5)  # Wait before retrying

try:
    producer.flush()
    producer.close()
    logger.info("Kafka producer closed.")
except Exception as e:
    logger.error(f"Error closing producer: {e}")
    logger.info("Kafka producer closed.")


