import json, re, threading, requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse

rows = json.load(open('work/chartops.json'))
doms = {}
for r in rows:
    doms.setdefault(r['Alan adı'], {'firma': r['Firma'], 'web': r['Web sitesi'], 'live': r['_live']})
todo = [(d, v) for d, v in doms.items() if v['live']]
print('canlı site:', len(todo), '/', len(doms), flush=True)

HDRS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'}
BIMCO = re.compile(r'bimco', re.I)
LINKS = re.compile(r'(about|hakk|chi-siamo|qui-sommes|unternehmen|company|profile|membership|member|association|quality|certificat|accredit|partner|affilia|iso|policy|home|kurumsal|biz-kimiz)', re.I)
lock = threading.Lock(); out = []; n = [0]

def strip(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S | re.I)
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', h))

def work(item):
    dom, v = item
    res = {'domain': dom, 'firma': v['firma'], 'bimco': False, 'evidence': '', 'page': '', 'pages': 0}
    try:
        r = requests.get(v['web'] or 'https://%s/' % dom, headers=HDRS, timeout=20, allow_redirects=True)
    except Exception:
        r = None
    pages = []
    if r is not None and r.status_code < 400:
        pages.append((r.url, r.text or ''))
        links = re.findall(r'href=["\']([^"\'#]+)["\']', r.text or '', re.I)
        cands, seen = [], set()
        for l in links:
            if LINKS.search(l):
                u2 = urljoin(r.url, l)
                if dom.split('.')[-2] in urlparse(u2).netloc and u2 not in seen and not re.search(r'\.(pdf|jpg|png|zip|docx?|xlsx?)$', u2, re.I):
                    seen.add(u2); cands.append(u2)
        for u2 in cands[:5]:
            try:
                r2 = requests.get(u2, headers=HDRS, timeout=15)
                if r2.status_code == 200: pages.append((r2.url, r2.text or ''))
            except Exception:
                pass
    res['pages'] = len(pages)
    for url, html in pages:
        if BIMCO.search(html):
            txt = strip(html)
            m = BIMCO.search(txt)
            if m:
                res['bimco'] = True; res['page'] = url
                res['evidence'] = txt[max(0, m.start() - 110):m.start() + 110].strip()
                break
            else:
                res['bimco'] = True; res['page'] = url; res['evidence'] = '(sayfa kodunda/logo alt metninde BIMCO geçiyor)'
                break
    with lock:
        out.append(res); n[0] += 1
        if n[0] % 15 == 0: print(n[0], flush=True)

with ThreadPoolExecutor(max_workers=14) as ex:
    list(ex.map(work, todo))
json.dump(out, open('work/bimco.json', 'w'), ensure_ascii=False)
hit = [o for o in out if o['bimco']]
print('BIMCO referansı bulunan:', len(hit))
for o in hit: print(' +', o['firma'], '|', o['domain'])
