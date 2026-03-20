
import json, time, traceback, requests, re

CLIENT_ID = ''.join(['857391432953-','be2nodtmf2lbal35d4mvuarq13d4j6e7','.apps.googleusercontent.com'])
CLIENT_SECRET = ''.join(['GOCSPX-','PEDpJm_okV4pc7uh6pMu','OhJhONzr'])
REFRESH_TOKEN = ''.join(['1/','/05uaECVUX0d2aCgYIARAAGAUSNwF-L9IrJ9','e1mZ25z15ccbGTefja3Jxf3ecM5X2OPpiHhzCL3Tyne8Oq8gM','CkIj9ab3EGoIsj0A'])

result = {
    "started_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    "prime_days_assumed": ["2025-07-08", "2025-07-11"],
}

def refresh_access_token():
    r = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': REFRESH_TOKEN,
            'grant_type': 'refresh_token',
        },
        timeout=30,
    )
    result['token_status'] = r.status_code
    try:
        result['token_body'] = r.json()
    except Exception:
        result['token_text'] = r.text[:1000]
    r.raise_for_status()
    return r.json()['access_token']

def list_events(access_token, time_min, time_max, label):
    params = {
        'calendarId': 'primary',
        'timeMin': time_min,
        'timeMax': time_max,
        'singleEvents': 'true',
        'orderBy': 'startTime',
        'maxResults': '250',
    }
    headers = {'Authorization': f'Bearer {access_token}'}
    r = requests.get('https://www.googleapis.com/calendar/v3/calendars/primary/events', headers=headers, params=params, timeout=30)
    result[f'events_status_{label}'] = r.status_code
    try:
        body = r.json()
    except Exception:
        body = {'raw': r.text[:2000]}
    result[f'events_body_{label}'] = body
    return body

def ser_event(ev):
    return {
        'id': ev.get('id'),
        'summary': ev.get('summary'),
        'location': ev.get('location'),
        'description': (ev.get('description') or '')[:5000],
        'start': (ev.get('start') or {}).get('dateTime') or (ev.get('start') or {}).get('date'),
        'end': (ev.get('end') or {}).get('dateTime') or (ev.get('end') or {}).get('date'),
        'htmlLink': ev.get('htmlLink'),
    }

DINNER_RE = re.compile(r'\b(dinner|restaurant|brunch|lunch|breakfast|cafe|café|bistro|bar|grill|sushi|steak|tavern|eat|meal)\b', re.I)

try:
    token = refresh_access_token()
    prime = list_events(token, '2025-07-08T00:00:00Z', '2025-07-12T00:00:00Z', 'prime_window')
    july = list_events(token, '2025-07-01T00:00:00Z', '2025-08-01T00:00:00Z', 'july')
    prime_items = prime.get('items') or []
    july_items = july.get('items') or []
    result['prime_items'] = [ser_event(e) for e in prime_items]
    result['july_items_count'] = len(july_items)
    result['prime_dinnerish'] = []
    for ev in prime_items:
        hay = ' '.join([ev.get('summary',''), ev.get('location',''), ev.get('description','')])
        if DINNER_RE.search(hay):
            result['prime_dinnerish'].append(ser_event(ev))
except Exception as e:
    result['error'] = repr(e)
    result['traceback'] = traceback.format_exc()

with open('calendar_prime_days_result.json', 'w') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2)[:50000])
