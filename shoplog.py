import argparse
import csv
import datetime as dt
from pathlib import Path

DATA_DIR = Path("data")
CSV_PATH = DATA_DIR / "maintenance.csv"

FIELDNAMES = [
    "date",
    "vehicle",
    "odometer",
    "job",
    "parts",
    "cost",
    "who",
    "torque_notes",
    "interval_miles",
    "interval_months",
    "next_due_miles",
    "next_due_date",
]


def ensure_csv():
    DATA_DIR.mkdir(exist_ok=True, parents=True)
    if not CSV_PATH.exists():
        with CSV_PATH.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def parse_date(s):
    return dt.date.fromisoformat(s)


def fmt_date(d):
    return d.isoformat()


def add_months(d, months):
    y, m = divmod((d.year * 12 + d.month - 1) + months, 12)
    y, m = y, m + 1
    day = min(
        d.day,
        (dt.date(y + (m // 12), ((m - 1) % 12) + 1, 1) - dt.timedelta(days=1)).day,
    )
    return dt.date(y, m, day)


def cmd_add(args):
    ensure_csv()
    today = parse_date(args.date) if args.date else dt.date.today()
    next_due_miles = ""
    next_due_date = ""
    if args.interval_miles and args.odometer is not None:
        next_due_miles = int(args.odometer) + int(args.interval_miles)
    if args.interval_months:
        next_due_date = fmt_date(add_months(today, int(args.interval_months)))

    row = {
        "date": fmt_date(today),
        "vehicle": args.vehicle,
        "odometer": args.odometer,
        "job": args.job,
        "parts": args.parts or "",
        "cost": f"{float(args.cost):.2f}" if args.cost is not None else "",
        "who": args.who or "Self",
        "torque_notes": args.torque or "",
        "interval_miles": args.interval_miles or "",
        "interval_months": args.interval_months or "",
        "next_due_miles": next_due_miles,
        "next_due_date": next_due_date,
    }
    with CSV_PATH.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
    print(
        f"Added: {row['date']} {row['vehicle']} - {row['job']} @ {row['odometer']} mi"
    )


def read_rows():
    ensure_csv()
    with CSV_PATH.open("r", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def cmd_list(args):
    rows = read_rows()
    rows = [r for r in rows if (not args.vehicle or r["vehicle"] == args.vehicle)]
    rows = sorted(rows, key=lambda r: (r["vehicle"], r["date"]))
    for r in rows:
        print(
            f"{r['date']} | {r['vehicle']} | {r['odometer']} mi | {r['job']} | ${r['cost']} | next due: {r['next_due_miles']} mi / {r['next_due_date']}"
        )


def cmd_due(args):
    rows = read_rows()
    today = parse_date(args.date_today) if args.date_today else dt.date.today()
    miles_now = args.miles_now
    out = []
    for r in rows:
        due_m = r["next_due_miles"]
        due_d = r["next_due_date"]
        due_flags = []
        if miles_now is not None and due_m:
            try:
                if int(due_m) <= int(miles_now):
                    due_flags.append("miles")
            except ValueError:
                pass
        if due_d:
            try:
                if parse_date(due_d) <= today:
                    due_flags.append("date")
            except ValueError:
                pass
        if due_flags and (not args.vehicle or r["vehicle"] == args.vehicle):
            out.append((r, due_flags))
    if not out:
        print("Nothing due. Nice!")
    else:
        for r, flags in sorted(out, key=lambda x: (x[0]["vehicle"], x[0]["date"])):
            flag_txt = "/".join(flags)
            print(
                f"DUE[{flag_txt}] {r['vehicle']} | {r['job']} | last {r['date']} @ {r['odometer']} mi | next {r['next_due_miles']} / {r['next_due_date']}"
            )


def cmd_summary(_args):
    rows = read_rows()
    by_vehicle = {}
    by_job = {}
    total = 0.0
    for r in rows:
        v = r["vehicle"]
        j = r["job"]
        c = float(r["cost"]) if r["cost"] else 0.0
        total += c
        by_vehicle[v] = by_vehicle.get(v, 0.0) + c
        by_job[j] = by_job.get(j, 0.0) + c
    print("=== Cost by vehicle ===")
    for v, c in sorted(by_vehicle.items()):
        print(f"{v}: ${c:.2f}")
    print("\n=== Cost by job ===")
    for j, c in sorted(by_job.items(), key=lambda x: -x[1]):
        print(f"{j}: ${c:.2f}")
    print(f"\nTotal: ${total:.2f}")


def build_parser():
    p = argparse.ArgumentParser(
        description="ShopLog: simple vehicle maintenance ledger"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="add a maintenance entry")
    a.add_argument("--date", help="YYYY-MM-DD (default today)")
    a.add_argument("--vehicle", required=True)
    a.add_argument("--odometer", type=int, required=True)
    a.add_argument("--job", required=True)
    a.add_argument("--parts")
    a.add_argument("--cost", type=float)
    a.add_argument("--who", choices=["Self", "Shop"])
    a.add_argument("--torque")
    a.add_argument("--interval-miles", type=int)
    a.add_argument("--interval-months", type=int)
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="list entries")
    l.add_argument("--vehicle")
    l.set_defaults(func=cmd_list)

    d = sub.add_parser("due", help="show due items by mileage/date")
    d.add_argument("--vehicle")
    d.add_argument("--miles-now", type=int)
    d.add_argument("--date-today")
    d.set_defaults(func=cmd_due)

    s = sub.add_parser("summary", help="cost summary by vehicle and job")
    s.set_defaults(func=cmd_summary)

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
