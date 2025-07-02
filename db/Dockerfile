# Use official slim Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies & SQL Server ODBC Driver
RUN apt-get update && \
    apt-get install -y \
        curl \
        gnupg \
        wget \
        unixodbc \
        unixodbc-dev \
        libgssapi-krb5-2 \
        gcc \
        g++ \
        libssl-dev \
        libffi-dev \
        unzip && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Run the FastAPI app
CMD ["uvicorn", "db:app", "--host", "0.0.0.0", "--port", "8003"]
