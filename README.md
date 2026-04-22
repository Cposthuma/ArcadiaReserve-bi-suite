# mtg-bi-suite

Deze repository bevat een Streamlit-dashboard om CardMarket orders, verkochte artikelen en kosten te visualiseren.

## Wat is aangepast

Het dashboard kan nu lokaal draaien met lokale databestanden (standaard), in plaats van alleen via de cloud/S3.
Daarnaast is Docker toegevoegd zodat je het eenvoudig in een Docker repository/registry kunt hosten en daarna kunt deployen.

---

## 1) Lokaal draaien zonder cloud (direct op je machine)

### Vereisten
- Python 3.11+
- Pip

### Installeren en starten
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Lokale data plaatsen
Plaats de volgende bestanden in de map `data/`:
- `data/cardmarket_orders_data.csv`
- `data/cardmarket_articles_sold.csv`
- `data/Expenses.ods`

Standaard draait de app met:
- `DATA_SOURCE=local`
- `DATA_DIR=data`

Wil je toch S3 gebruiken, zet dan:
```bash
export DATA_SOURCE=s3
streamlit run streamlit_app.py
```

---

## 2) Draaien met Docker (lokaal)

### Build
```bash
docker build -t arcadiareserve-bi-suite:latest .
```

### Run
```bash
docker run --rm -p 8501:8501 \
  -e DATA_SOURCE=local \
  -e DATA_DIR=/app/data \
  -v $(pwd)/data:/app/data \
  arcadiareserve-bi-suite:latest
```

Open daarna: http://localhost:8501

---

## 3) Draaien met Docker Compose

```bash
docker compose up --build
```

Dit gebruikt `docker-compose.yml` met:
- poort `8501:8501`
- lokale data mount `./data:/app/data`
- `DATA_SOURCE=local`

---

## 4) Hosten via Docker repository (registry)

Voorbeeld met Docker Hub:

```bash
docker tag arcadiareserve-bi-suite:latest <dockerhub-user>/arcadiareserve-bi-suite:latest
docker push <dockerhub-user>/arcadiareserve-bi-suite:latest
```

Deploy daarna op je server met dezelfde environment variables en volume-mount voor `/app/data`.

---

## Environment variables

- `DATA_SOURCE`:
  - `local` (standaard): leest uit lokale bestanden
  - `s3`: leest uit publieke S3-bestanden
- `DATA_DIR`:
  - map waar lokale databestanden staan
  - standaard `data` (of `/app/data` in Docker)

