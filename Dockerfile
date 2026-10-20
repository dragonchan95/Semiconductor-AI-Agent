FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 STATE_DIR=/state APP_ENV=production
COPY requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY app app
COPY static static
COPY data data
COPY scripts scripts
RUN python scripts/download_secom.py && useradd --uid 10001 --create-home copilot && mkdir /state && chown 10001 /state
USER 10001
EXPOSE 8700
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8700"]
