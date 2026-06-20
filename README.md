# ArcadiaReserve BI Suite

Een lokaal Streamlit-dashboard voor Cardmarket-data. De app leest exports uit lokale bestanden en heeft geen S3/AWS-configuratie nodig.

## Wat je krijgt

- Volledig lokaal dashboard op basis van bestanden in `data/`
- Docker Compose setup met een read-only mount naar de lokale data-map
- Automatische kolomnormalisatie voor:
  - orders
  - sold articles
  - expenses
- Pagina's:
  - Home
  - Orders Overview
  - Analytics
  - Costs
  - Sold Articles
  - Settings

## Data plaatsen

Plaats exports in:

- `data/orders/`
- `data/articles/`
- `data/expenses/`

Bestanden direct in `data/` worden ook gelezen voor backward compatibility.

De Docker image bevat bewust geen exports. `docker-compose.yml` mount je lokale `./data` map als `/app/data` in de container.

## Lokaal runnen zonder Docker

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Runnen met Docker Compose

```bash
docker compose up --build
```

Open daarna `http://localhost:8501`.

Wil je een andere lokale data-map gebruiken, pas dan de volume-regel in `docker-compose.yml` aan:

```yaml
volumes:
  - /pad/naar/jouw/data:/app/data:ro
```
