# Financial precision

All money, prices, and quantities use `decimal.Decimal`; binary floating point is not used. Currency is fixed to EGP. Database prices and costs use `NUMERIC(20,4)`, monetary totals use `NUMERIC(20,2)`, and quantities use `NUMERIC(20,4)`.

Intermediate calculations remain unrounded. Reporting boundaries apply `ROUND_HALF_EVEN`: `quantize_price` produces four decimal places and `quantize_money` produces two. API schemas serialize Decimal values as strings. Transactions are processed by `(executed_at, sequence)`, with the server-generated sequence resolving same-timestamp ties in insertion order.
