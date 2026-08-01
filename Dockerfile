ARG BASE_REGISTRY=docker.io/library

# Stage 1: dependências
FROM ${BASE_REGISTRY}/python:3.9-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime sem root
ARG BASE_REGISTRY=docker.io/library
FROM ${BASE_REGISTRY}/python:3.9-slim
RUN useradd --uid 1000 --create-home appuser
WORKDIR /app
COPY --from=builder --chown=1000:1000 /root/.local /home/appuser/.local
COPY --chown=1000:1000 . .
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
USER 1000
EXPOSE 8005
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "app:app"]
