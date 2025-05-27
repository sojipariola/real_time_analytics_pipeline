# Step 1: Use a lightweight base image
FROM python:3.11-slim

# Step 2: Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app

# Step 3: Create working directory
WORKDIR $APP_HOME

# Step 4: Install OS dependencies
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

# Step 5: Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the actual app code
COPY . .

# Step 7: Set entrypoint or command
CMD ["python", "kafka_producer.py"]

# Rest of the Dockerfile remains the same...
EXPOSE 9092

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER 1001:1001

HEALTHCHECK CMD curl --fail http://localhost:9092/ || exit 1

LABEL maintainer="Olusoji Omopariola" \
      version="1.0" \
      description="Kafka Producer Dockerfile"

LABEL org.opencontainers.image.title="Kafka Producer" \
      org.opencontainers.image.description="A Kafka producer application" \
      org.opencontainers.image.version="1.0" \
      org.opencontainers.image.authors="Olusoji Omopariola <sojipariola@gmail.com>"