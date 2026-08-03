FROM python:3.11-slim

# Install RMR library (OSC RIC dependency)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    dpkg \
    && wget --content-disposition https://packagecloud.io/o-ran-sc/release/packages/debian/stretch/rmr_4.9.0_amd64.deb/download.deb \
    && dpkg -i rmr_4.9.0_amd64.deb \
    && rm -f rmr_4.9.0_amd64.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app

# Environment variables
ENV RMR_SEED_RT=/app/configs/uta_rtg.rt
ENV PYTHONPATH=/app/src

EXPOSE 8080 8081

CMD ["python", "src/rdl_xapp.py"]
