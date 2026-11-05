import json, re, threading, requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

prev = {o['domain']: o for o in json.load(open('work/bimco.json'))}
todo = [d for d, o in prev.items() if not o['bimco']]
print('derin tarama:', len(todo), flush=True)
HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
BIMCO = re.compile(r'bimco', re.I)
lock = threading.Lock(); out = []; n = [0]

def strip(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))

def get(u, t=15):
    try:
        r = requests.get(u, headers=HDRS, timeout=t, allow_redirects=True)
        return r if r.status_code < 400 else None
    except Exception:
        return None

def work(dom):
    res = {'domain': dom, 'bimco': False, 'evidence': '', 'page': '', 'pages': 0}
    urls, seen = [], set()
    r = get('https://%s/' % dom) or get('https://www.%s/' % dom)
    if r is None:
        res['pages'] = 0; 
        with lock: out.append(res); n[0] += 1
        return
    base = r.url
    pool = [(base, r.text or '')]
    links = re.findall(r'href=["\']([^"\'#]+)["\']', r.text or '', re.I)
    host = urlparse(base).netloc
    KEY = re.compile(r'(about|hakk|company|profile|quality|certificat|accredit|member|associa|partner|iso|policy|service|chartering|operation|fleet|contact|kurumsal|chi-siamo|unternehmen|qui-sommes|nosotros|over-ons)', re.I)
    cands = []
    for l in links:
        u2 = urljoin(base, l)
        if urlparse(u2).netloc != host or u2 in seen: continue
        if re.search(r'\.(jpg|png|gif|svg|zip|docx?|xlsx?|mp4)$', u2, re.I): continue
        seen.add(u2)
        if KEY.search(u2): cands.append(u2)
    # sitemap fallback
    if len(cands) < 4:
        sm = get('https://%s/sitemap.xml' % dom, 12)
        if sm is not None:
            for loc in re.findall(r'<loc>([^<]+)</loc>', sm.text or '')[:60]:
                if KEY.search(loc) and loc not in seen:
                    seen.add(loc); cands.append(loc)
    for u2 in cands[:12]:
        r2 = get(u2, 12)
        if r2 is not None: pool.append((r2.url, r2.text or ''))
    res['pages'] = len(pool)
    for url, html in pool:
        if BIMCO.search(html):
            txt = strip(html); m = BIMCO.search(txt)
            res['bimco'] = True; res['page'] = url
            res['evidence'] = txt[max(0, m.start() - 120):m.start() + 120].strip() if m else '(sayfa kodunda/logoda BIMCO)'
            break
    with lock:
        out.append(res); n[0] += 1
        if n[0] % 10 == 0: print(n[0], flush=True)

with ThreadPoolExecutor(max_workers=12) as ex:
    list(ex.map(work, todo))
json.dump(out, open('work/bimco2.json', 'w'), ensure_ascii=False)
hit = [o for o in out if o['bimco']]
print('derin taramada bulunan:', len(hit))
for o in hit: print(' +', o['domain'], '|', o['evidence'][:140])
