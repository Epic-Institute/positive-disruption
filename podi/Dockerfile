FROM python:3.9-slim-buster

WORKDIR /app

# Copy requirements.txt from the same directory as Dockerfile
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y gcc
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn

# Copy app and data
COPY assets ./assets/
COPY app.py .
COPY data/energy_output.parquet ./data/
COPY data/emissions_output_co2e.parquet ./data/
COPY data/climate_output_concentration.parquet ./data/
COPY data/climate_output_temperature.parquet ./data/
COPY data/climate_output_forcing.parquet ./data/
COPY data/technology_adoption_output.parquet ./data/


CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:server