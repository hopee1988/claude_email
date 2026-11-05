import json, re, sys, os, time, threading
import requests
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin, urlparse

comps = json.load(open('work/companies.json'))
domains = sorted({c['domain'] for c in comps})
OUT = 'work/checked.jsonl'
done = set()
if os.path.exists(OUT):
    for line in open(OUT):
        try: done.add(json.loads(line)['domain'])
        except Exception: pass
todo = [d for d in domains if d not in done]
print('domains', len(domains), 'todo', len(todo), flush=True)

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
CONTACT = re.compile(r'(contact|kontakt|contatti|contacto|contato|iletis|about|team|crew|impressum|imprint|contacts|nous|people|staff|company)', re.I)
HDRS = {'User-Agent': 'Mozilla/5.0 (compatible; data-verification-bot)', 'Accept-Language': 'en,*'}
lock = threading.Lock()
f = open(OUT, 'a')
cnt = [0]

def sess():
    s = requests.Session()
    s.mount('https://', HTTPAdapter(max_retries=0, pool_maxsize=4))
    s.mount('http://', HTTPAdapter(max_retries=0, pool_maxsize=4))
    return s

def get(s, url, t=12):
    try:
        r = s.get(url, headers=HDRS, timeout=t, allow_redirects=True)
        return r
    except Exception as e:
        return None

def work(dom):
    s = sess()
    res = {'domain': dom, 'site': '', 'status': 0, 'title': '', 'emails_found': [], 'pages': 0, 'err': ''}
    r = None
    for u in ('https://www.%s/' % dom, 'https://%s/' % dom, 'http://www.%s/' % dom):
        r = get(s, u)
        if r is not None and r.status_code < 500:
            break
    if r is None:
        res['err'] = 'unreachable'
    else:
        res['status'] = r.status_code
        res['site'] = r.url
        html = r.text if r.text else ''
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.S | re.I)
        if m: res['title'] = re.sub(r'\s+', ' ', m.group(1))[:120].strip()
        found = set(e.lower() for e in EMAIL_RE.findall(html))
        res['pages'] = 1
        # contact pages
        links = re.findall(r'href=["\']([^"\'#]+)["\']', html, re.I)
        cands, seen = [], set()
        for l in links:
            if CONTACT.search(l):
                u2 = urljoin(r.url, l)
                if urlparse(u2).netloc.endswith(dom.split('.')[-2] + '.' + dom.split('.')[-1]) or dom in urlparse(u2).netloc:
                    if u2 not in seen and not re.search(r'\.(pdf|jpg|png|zip|docx?)$', u2, re.I):
                        seen.add(u2); cands.append(u2)
        for u2 in cands[:4]:
            r2 = get(s, u2, 10)
            if r2 is not None and r2.status_code == 200:
                res['pages'] += 1
                found |= set(e.lower() for e in EMAIL_RE.findall(r2.text or ''))
        found = {e for e in found if not re.search(r'\.(png|jpg|jpeg|gif|webp|svg|css|js)$', e)
                 and not e.startswith(('sentry', 'wixpress', 'example@', 'user@', 'name@', 'email@', 'info@domain'))
                 and 'sentry.io' not in e and 'wixpress' not in e}
        res['emails_found'] = sorted(found)[:60]
    with lock:
        f.write(json.dumps(res, ensure_ascii=False) + '\n'); f.flush()
        cnt[0] += 1
        if cnt[0] % 50 == 0: print('done', cnt[0], '/', len(todo), flush=True)

from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=28) as ex:
    list(ex.map(work, todo))
print('ALL DONE', cnt[0], flush=True)
