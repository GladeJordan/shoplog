# ShopLog
A dead-simple maintenance log for your vehicles. Keep a CSV ledger of work done (oil, diff, t-case, plugs, etc.), and use a tiny CLI to **add** entries, see what's **due**, and print **summaries**.

## Quick start
```bash
python shoplog.py add --vehicle "1985 F-150" --odometer 124350 \
    --job "NP208 fluid change" --parts "ATF Dexron III x2" --cost 24.98 \
    --torque "Drain 15-30 ft-lb, Fill 15-30 ft-lb" --interval-miles 30000 --interval-months 36

python shoplog.py list --vehicle "1985 F-150"
python shoplog.py due --vehicle "1985 F-150" --miles-now 124500 --date-today 2025-10-15
python shoplog.py summary
```