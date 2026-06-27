"""
M&E Fresh Eggs — Daily Report Generator (Presentable Telegram Format)
"""
import json, sys
from collections import defaultdict
from urllib.request import Request, urlopen
import binascii
from datetime import datetime, timedelta

h1 = "65794a68624763694f694a49557a49314e694973496e523563434936496b705856434a392e65794a7063334d694f694a7a64584268596d467a5a534973496e4a6c5a694936"
h2 = "496d3577623268355a5846755957783063484636625731736257567149697769636d39735a534936496d4675623234694c434a70595851694f6a45334f4441774f446b314e6a59314e7a513566512e"
h3 = "364478662d47503653435254697a6d6e4642504e597141654d4161586645464170354c4679676e71365938"
hex_all = h1 + h2 + h3
raw = binascii.unhexlify(hex_all)
SUPA_KEY = raw.decode('utf-8')
URL = "https://npohyeqnaltpqzmmlmej.supabase.co"
HEADERS = {"apikey": SUPA_KEY, "Authorization": "Bearer " + SUPA_KEY}


def fetch(url_suffix):
    req = Request(URL + url_suffix, headers=HEADERS)
    return json.loads(urlopen(req, timeout=20).read())


egg_sizes = fetch("/rest/v1/egg_sizes?select=id,name,sort_order&order=sort_order.asc")
size_map = {es["id"]: es for es in egg_sizes}

if len(sys.argv) > 1:
    REPORT_DATE = sys.argv[1]
else:
    yesterday = datetime.utcnow() + timedelta(hours=8) - timedelta(days=1)
    REPORT_DATE = yesterday.strftime("%Y-%m-%d")

day_name = datetime.strptime(REPORT_DATE, "%Y-%m-%d").strftime("%A")

sales = fetch(f"/rest/v1/sales?select=id,egg_size_id,quantity,unit,tray_size,total_amount,sale_date,sale_time&sale_date=eq.{REPORT_DATE}&order=sale_time")
for s in sales:
    esid = s.get("egg_size_id")
    if esid and esid in size_map:
        s["egg_size_name"] = size_map[esid]["name"]

by_size = defaultdict(lambda: {"qty": 0, "revenue": 0.0, "txns": 0, "trays": 0, "pieces": 0})
total_rev = 0.0
total_qty = 0
for s in sales:
    size = s.get("egg_size_name", "?")
    amt = float(s.get("total_amount") or 0)
    by_size[size]["revenue"] += amt
    by_size[size]["txns"] += 1
    total_rev += amt
    if s.get("unit") == "tray":
        q = s["quantity"] * (s.get("tray_size") or 30)
        by_size[size]["trays"] += s["quantity"]
    else:
        q = s["quantity"]
        by_size[size]["pieces"] += s["quantity"]
    by_size[size]["qty"] += q
    total_qty += q

size_order = ["Peewee", "Pullet", "Small", "Medium", "Large", "Extra Large", "Jumbo"]

inv = fetch("/rest/v1/inventory?select=*&order=egg_size_id.asc")
inv_lines = []
for i in sorted(inv, key=lambda x: size_map.get(x.get("egg_size_id"), {}).get("sort_order", 99)):
    es = size_map.get(i.get("egg_size_id"), {})
    qty = i.get("quantity_on_hand", 0)
    alert = " OUT" if qty == 0 else (" LOW" if qty <= 30 else "")
    inv_lines.append(f"  {es.get('name','?')}: {qty} pcs{alert}")

pr = fetch("/rest/v1/price_settings?select=*&order=egg_size_id.asc")
price_lines = []
for p in sorted(pr, key=lambda x: size_map.get(x.get("egg_size_id"), {}).get("sort_order", 99)):
    es = size_map.get(p.get("egg_size_id"), {})
    price_lines.append(f"  {es.get('name','?')}: {float(p.get('price_per_piece',0)):.2f}/pc | {float(p.get('price_per_tray',0)):.2f}/tray")

exp = fetch(f"/rest/v1/expenses?select=*&expense_date=eq.{REPORT_DATE}")
total_exp = sum(float(e.get("amount", 0)) for e in exp)
exp_lines = []
for e in exp:
    exp_lines.append(f"  {e.get('category','?')}: {float(e.get('amount',0)):.2f} - {e.get('description','')}")

deliv = fetch(f"/rest/v1/deliveries?select=*&delivery_date=eq.{REPORT_DATE}")
total_deliv = sum(float(d.get("total_cost", 0)) for d in deliv)
deliv_lines = []
for d in deliv:
    es = size_map.get(d.get("egg_size_id"), {})
    deliv_lines.append(f"  {es.get('name','?')}: {d.get('quantity','?')} trays - {float(d.get('total_cost',0)):.2f}")

d30 = (datetime.utcnow() + timedelta(hours=8) - timedelta(days=30)).strftime("%Y-%m-%d")
trend = fetch(f"/rest/v1/sales?select=sale_date,total_amount&sale_date=gte.{d30}&order=sale_date.asc")
daily_rev = defaultdict(float)
for t in trend:
    daily_rev[t.get("sale_date", "")] += float(t.get("total_amount", 0))
sorted_days = sorted(daily_rev.keys())
last7 = [daily_rev[d] for d in sorted_days[-7:]] if len(sorted_days) >= 7 else []
prev7 = [daily_rev[d] for d in sorted_days[-14:-7]] if len(sorted_days) >= 14 else []
last7_sum = sum(last7)
prev7_sum = sum(prev7)
wow_str = ""
if prev7_sum:
    chg = (last7_sum - prev7_sum) / prev7_sum * 100
    wow_str = f"WoW: +{chg:.1f}%" if chg >= 0 else f"WoW: {chg:.1f}%"

print(f"M&E Fresh Eggs - Daily Report")
print(f"{day_name}, {REPORT_DATE}")
print()

print(f"[ Sales Breakdown ]")
print(f"Size          Qty    Revenue")
print(f"-" * 36)
for sz in size_order:
    d = by_size.get(sz)
    if d:
        label = f"{sz} ({d['txns']})"
        print(f"{label:<16}{d['qty']:>5}   PHP {d['revenue']:>9,.2f}")
    else:
        print(f"{sz:<16}    -          -")
print(f"-" * 36)
label_t = f"TOTAL ({len(sales)} txns)"
print(f"{label_t:<16}{total_qty:>5}   PHP {total_rev:>9,.2f}")
if total_rev and sales:
    print(f"Avg: PHP {total_rev / len(sales):,.2f}/txn")
print()

print(f"[ Inventory ]" )
for line in inv_lines:
    print(line)

print()
print(f"[ Pricing ]" )
for pl in price_lines:
    print(pl)

if exp:
    print()
    print(f"[ Expenses ({len(exp)}) - PHP {total_exp:,.2f} ]" )
    for el in exp_lines:
        print(f"  {el}")

if deliv:
    print()
    print(f"[ Deliveries ({len(deliv)}) - PHP {total_deliv:,.2f} ]" )
    for dl in deliv_lines:
        print(f"  {dl}")

print()
print(f"[ Financial Summary ]" )
print(f"  Revenue:    PHP {total_rev:>10,.2f}")
print(f"  Expenses:   PHP {total_exp:>10,.2f}")
net = total_rev - total_exp
print(f"  Net Profit: PHP {net:>10,.2f}")
if total_rev:
    margin = (net / total_rev) * 100
    print(f"  Margin:     {margin:>10.1f}%")

if last7:
    print()
    print(f"[ 7-Day Trend ]" )
    max_val = max(last7) if last7 else 1
    for d in sorted_days[-7:]:
        bar_len = max(1, int(daily_rev[d] / (max_val or 1) * 10))
        bar = "#" * bar_len
        print(f"  {d}: PHP {daily_rev[d]:>8,.2f}  {bar}")
    if wow_str:
        print(f"  {wow_str}")

print()
print(f"Report complete")
