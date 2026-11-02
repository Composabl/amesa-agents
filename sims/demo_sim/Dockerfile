######################################################
# Amesa sim-demo (counter sim)
######################################################
FROM python:3.11-slim

WORKDIR /opt/amesa

ARG AMESA_API_WHEEL_PATH="artifacts/amesa_api-*.whl"
ARG AMESA_CORE_WHEEL_PATH="artifacts/amesa_core-*.whl"
ARG AMESA_SIM_DEMO_WHEEL_PATH="artifacts/amesa_sim_demo-*.whl"

WORKDIR /opt/amesa

RUN apt update && apt install -y unzip tree && rm -rf /var/lib/apt/lists/*
RUN ln -s /usr/bin/python3 /usr/bin/python

RUN pip install --no-cache-dir --upgrade pip redis

COPY ${AMESA_API_WHEEL_PATH} /tmp/wheels/
COPY ${AMESA_CORE_WHEEL_PATH} /tmp/wheels/
COPY ${AMESA_SIM_DEMO_WHEEL_PATH} /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/amesa_api-*.whl /tmp/wheels/amesa_core-*.whl /tmp/wheels/amesa_sim_demo-*.whl && rm -rf /tmp/wheels

# Copy sim module and main.py
COPY sim/ /opt/amesa/sim/
COPY main.py /opt/amesa/main.py

ENV PYTHONUNBUFFERED=1

COPY docker/entrypoint.sh /usr/local/bin/amesa-sim-entrypoint.sh
RUN chmod +x /usr/local/bin/amesa-sim-entrypoint.sh

EXPOSE 1337
ENTRYPOINT [ "/usr/bin/bash", "/usr/local/bin/amesa-sim-entrypoint.sh" ]