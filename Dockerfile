FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src/ ./src/
COPY data/ ./data/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"
    
# Copy Streamlit configuration
COPY .streamlit/ ./.streamlit/

# Streamlit listens on 8501 by default
EXPOSE 8501

# Run as non-root for security
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["streamlit", "run", "src/bwace/app/main.py", \
            "--server.port=8501", \
            "--server.address=0.0.0.0", \
            "--server.enableCORS=false", \
            "--server.enableXsrfProtection=false"]
