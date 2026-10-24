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
# Sem pip no runtime: ele só é usado no build (stage 1). Tirar daqui remove o
# certifi que o pip traz embutido (GHSA-6q48-6c7w-9gw2, CRÍTICA no Trivy) e um
# gerenciador de pacotes que a aplicação não usa.
RUN python -m pip uninstall --yes --no-cache-dir pip \
    && useradd --uid 1000 --create-home appuser
WORKDIR /app
# Dependências e código ficam com dono root, sem --chown: o usuário do app
# (1000) só lê e executa. Se alguém tomar o processo, não consegue alterar
# o código nem as bibliotecas (Sonar docker:S6504).
COPY --from=builder /root/.local /home/appuser/.local
# Só o código da aplicação: testes, configs de CI e docs ficam de fora
# (ver .dockerignore).
COPY app.py .
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER 1000
EXPOSE 8005
CMD ["gunicorn", "--bind", "0.0.0.0:8005", "--access-logfile", "-", "app:app"]
