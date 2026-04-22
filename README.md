# ArcadiaReserve BI Suite

Dit project visualiseert CardMarket orders, sold articles en kosten in een Streamlit dashboard.

## ✅ Wat is aangepast

- Klaar voor hosting in een Docker registry/repo (met `Dockerfile` + `docker-compose.yml`).
- Dashboard draait op **lokale bestanden** uit de `data/` map.

---

## Lokale data (standaard)

Plaats je databestanden in `./data` (of in de submappen hieronder):

- `data/orders/` → orders / PurchaseData exports (`.csv`)
- `data/articles/` → sold articles / SalesData exports (`.csv`)
- `data/expenses/` → expenses (`.csv`, `.xlsx`, `.xls`, `.ods`)

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
  -e DATA_DIR=/app/data \
  -v "$(pwd)/data:/app/data:ro" \
  arcadia-bi-suite:latest
```

---

## Environment configuratie

Gebruik `.env.example` als referentie.

### Lokale modus (default)

- `DATA_DIR=./data` (of `/app/data` in Docker)

---

## Publiceren naar een Docker repository

Voorbeeld met Docker Hub:

```bash
docker build -t <dockerhub-user>/arcadia-bi-suite:latest .
docker push <dockerhub-user>/arcadia-bi-suite:latest
```

Daarna kan je dezelfde image overal deployen.
