# Local data files

Deze map wordt door Docker gemount als `/app/data`.

Plaats Cardmarket exports bij voorkeur zo:

- `data/orders/` voor `Sold Shipments-byPurchaseDate-*.csv`
- `data/articles/` voor `Sold Articles-byPurchaseDate-*.csv`
- `data/expenses/` voor losse expenses of purchase exports (`.csv`, `.xlsx`, `.xls`, `.ods`)

De app kan oudere `Sold Orders-byPurchaseDate-*.csv` exports nog als fallback lezen, maar `Sold Shipments` + `Sold Articles` geeft de beste resultaten.

