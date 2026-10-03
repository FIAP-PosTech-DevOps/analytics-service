# BASE_REGISTRY permite trocar a origem das imagens base sem editar o
# Dockerfile. O default é o Docker Hub (usado pela CI e pelo build local).
ARG BASE_REGISTRY=docker.io/library

# Stage 1: instala as dependências isoladamente. Compilador e cache do pip
# ficam neste estágio e não entram na imagem final.
FROM ${BASE_REGISTRY}/python:3.13-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: runtime enxuto e sem root.
FROM ${BASE_REGISTRY}/python:3.13-slim
RUN useradd --uid 1000 --create-home appuser
WORKDIR /app
COPY --from=builder --chown=1000:1000 /root/.local /home/appuser/.local
# Só o código da aplicação: testes, configs de CI e docs ficam de fora
# (ver .dockerignore).
COPY --chown=1000:1000 app.py .
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER 1000
EXPOSE 8005
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "--access-logfile", "-", "app:app"]
