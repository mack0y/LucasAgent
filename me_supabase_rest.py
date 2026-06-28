import urllib.request, urllib.parse, json, sys
BASE = 'https://npohyeqnaltpqzmmlmej.supabase.co/rest/v1'
KEY = '***'
def api(method, rel, params=None, payload=None):
    url = f'{BASE}{rel}'
    if params:
        url += '?' + urllib.parse.urlencode(params)
    body = json.dumps(payload).encode('utf-8') if payload is not None else None
    headers = {
        'apikey': KEY,
        'Authorization': f'Bearer {KEY}',
        'Accept': 'application/json',
    }
    if body is not None:
        headers.update({'Content-Type': 'application/json', 'Prefer': 'return=representation'})
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode('utf-8')
        return r.status, (json.loads(raw) if raw else None)
print('login=', api('GET', '/egg_sizes', {'select': 'id,name', 'limit': '1'}))
r, d = api('POST', '/test_writes', {'supplier_id': '2', 'egg_size_id': '1', 'quantity': '1', 'unit': 'tray', 'tray_size': '30', 'cost_per_egg': '150', 'total_cost': '150', 'delivery_date': '2026-06-28', 'notes': 'probe write', 'payment_status': 'unpaid'})
print('probe=', r, d)
