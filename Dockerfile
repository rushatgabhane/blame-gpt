FROM python:3.13-slim

WORKDIR /app

# git + bash are required at runtime by services/github/local_repository.py
RUN apt-get update \
    && apt-get install -y --no-install-recommends git bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# single worker only: the app shares one sqlite connection and uses
# in-process locks and BackgroundTasks
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
