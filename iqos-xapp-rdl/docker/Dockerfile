# Stage 1: Build dependencies
FROM python:3.10-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    dpkg \
    gcc \
    python3-dev \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr_4.9.0_amd64.deb \
    && rm -f rmr_4.9.0_amd64.deb

WORKDIR /app
COPY requirements.txt requirements-ml.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt -r requirements-ml.txt

# Stage 2: Final runtime image
FROM python:3.10-slim

# Install RMR library in runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    dpkg \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr_4.9.0_amd64.deb \
    && rm -f rmr_4.9.0_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash xapp
USER xapp
WORKDIR /app

# Install wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements* ./
# Install as user (to /home/xapp/.local/bin)
RUN pip install --user --no-cache /wheels/*

# Copy source code and configs
COPY --chown=xapp:xapp src/ /app/src/
COPY --chown=xapp:xapp configs/ /app/configs/

# Environment variables
ENV RMR_SEED_RT=/app/configs/routes.rt
ENV PYTHONPATH=/app
ENV PATH="/home/xapp/.local/bin:${PATH}"

# Ports for HTTP and Metrics
EXPOSE 8080 8081

# Healthcheck
HEALTHCHECK --interval=10s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

# Start xApp
CMD ["python", "src/main.py"]
