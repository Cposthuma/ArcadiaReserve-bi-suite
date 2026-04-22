# ArcadiaReserve BI Suite (Rebuilt)

Deze repository is opnieuw opgebouwd met een eenvoudige, robuuste Streamlit-architectuur.

## Wat je krijgt

- Volledig lokaal dashboard op basis van bestanden in `data/`
- Automatische kolomnormalisatie voor:
  - orders
  - sold articles
  - expenses
- Nieuwe, consistente pagina's:
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

Bestanden in `data/` root worden ook gelezen.

## Lokaal runnen

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Met Docker Compose

```bash
docker compose up --build
```

Open daarna `http://localhost:8501`.
