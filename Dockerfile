# Use official Python slim image
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal system deps (curl only)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl (stable)
RUN curl -LO "https://dl.k8s.io/release/stable/bin/linux/amd64/kubectl" \
    && install -m 0755 kubectl /usr/local/bin/kubectl \
    && rm -f kubectl

# Install ArgoCD CLI
RUN curl -sSL -o /usr/local/bin/argocd \
    https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64 \
    && chmod +x /usr/local/bin/argocd

# copy requirements first for layer caching
COPY requirements.txt .

RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

# copy application code (dockerignore will exclude venv/.git)
COPY . .

# create a non-root user and set permissions
RUN groupadd -r k2sobot && useradd -r -g k2sobot k2sobot \
    && mkdir -p /app/logs \
    && chown -R k2sobot:k2sobot /app

USER k2sobot

EXPOSE 3000

CMD ["python3", "main.py"]