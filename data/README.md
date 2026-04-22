# Local data files

Deze map wordt door Docker gemount als `/app/data`.

Plaats exports bij voorkeur in de submappen:

- `data/orders/` voor Cardmarket order/purchase exports (`.csv`)
- `data/articles/` voor Cardmarket sold/sales exports (`.csv`)
- `data/expenses/` voor expenses (`.csv`, `.xlsx`, `.xls`, `.ods`)

De app ondersteunt ook nog steeds bestanden direct in `data/` voor backward compatibility.
