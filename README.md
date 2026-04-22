# ArcadiaReserve BI Suite

Dit project visualiseert CardMarket orders, sold articles en kosten in een Streamlit dashboard.

## ✅ Wat is aangepast

- Klaar voor hosting in een Docker registry/repo (met `Dockerfile` + `docker-compose.yml`).
- Dashboard draait nu standaard op **lokale bestanden** in plaats van cloud/S3.
- S3 blijft optioneel beschikbaar via environment variables.

---

## Lokale data (standaard)

Plaats je databestanden in `./data`:

- `cardmarket_orders_data.csv`
- `cardmarket_articles_sold.csv`
- `Expenses.ods`

Zie ook: `data/README.md`.

---

## Runnen met Docker Compose (aanbevolen)

```bash
docker compose up --build
```

Open daarna:

- http://localhost:8501

De container mount `./data` als read-only map in de app (`/app/data`).

---

## Runnen met alleen Docker

Build:

```bash
docker build -t arcadia-bi-suite:latest .
```

Run:

```bash
docker run --rm -p 8501:8501 \
  -e DATA_SOURCE=local \
  -e DATA_DIR=/app/data \
  -v "$(pwd)/data:/app/data:ro" \
  arcadia-bi-suite:latest
```

---

## Environment configuratie

Gebruik `.env.example` als referentie.

### Lokale modus (default)

- `DATA_SOURCE=local`
- `DATA_DIR=./data` (of `/app/data` in Docker)

### S3 modus (optioneel)

- `DATA_SOURCE=s3`
- `S3_BUCKET_NAME=...`
- `S3_REGION=...`

---

## Publiceren naar een Docker repository

Voorbeeld met Docker Hub:

```bash
docker build -t <dockerhub-user>/arcadia-bi-suite:latest .
docker push <dockerhub-user>/arcadia-bi-suite:latest
```

Daarna kan je dezelfde image overal deployen.
