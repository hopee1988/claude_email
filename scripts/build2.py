import json, re, sys, collections, html as _html
sys.path.insert(0, 'work')
from classify import clean_name, fallback_name, classify, classify2, owner_or_broker, activity, ACT
from parse import TLD_COUNTRY, PHONE_CC, COUNTRIES

comps = json.load(open('work/companies2.json'))
site = {}
for fn in ('work/checked.jsonl', 'work/retry.jsonl', 'work/checked2.jsonl'):
    for l in open(fn):
        r = json.loads(l); d = r['domain']
        prev = site.get(d)
        if prev is None or ((r.get('status') or 0) > 0 and (prev.get('status') or 0) == 0):
            site[d] = r

PARKED = re.compile(r'(domain (is )?for sale|buy this domain|parked|domain name|under construction|coming soon|website expired|sedo\b|godaddy|namecheap|default web site|apache2 (ubuntu|debian)|index of /|account suspended|site not found|hostgator|plesk|cpanel|bluehost|this site can|web hosting)', re.I)
SPAM = re.compile(r'(casino|bahis|betting|slot|poker|porn|escort|viagra|cialis|loan|crypto|forex signals|essay|pay ?day|replica|sex|dating|bet\b|bonus|gambling|jackpot|\bcbd\b|pharmacy)', re.I)
GEO_TR = re.compile(r'(brezilya|latin amerika|avrupa|asya|afrika|orta doğu|uzak doğu|akdeniz|karadeniz|baltık|kuzey|güney|bölgesi|yeni eklenen|liste|kişi bazlı|temaslar|firmalar|ek kişiler|diğer)', re.I)
GENERIC_NAME = re.compile(r'^(ltd|limited|yachts?|ship ?stores|ports? authority|class|survey|shipping|marine|maritime|yachting|chartering|brokers?|agency|agents?|office|sales|contact|info|genel|group|company|co|services?|solutions?|bu |ve |the )\b', re.I)

def base(dom):
    p = dom.split('.')
    b = p[-3] if (len(p) >= 3 and len(p[-2]) <= 3) else p[-2] if len(p) >= 2 else p[0]
    return re.sub(r'[^a-z0-9]', '', b.lower())

def norm(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def title_name(title):
    if not title: return ''
    t = re.split(r'\s*[\|–—\-·:;»•]\s*|\s{2,}', title)
    t = [x.strip() for x in t if len(x.strip()) >= 3]
    if not t: return ''
    t.sort(key=lambda x: (-1 if re.search(r'(Ltd|S\.?r\.?l|S\.?p\.?A|B\.?V|GmbH|A/S|ApS|\bAB\b|\bAS\b|Inc|LLC|Group|Shipping|Marine|Maritime|Yacht|Brokers?|Agency|Shipyard|Marina)', x, re.I) else 0, len(x)))
    return t[0][:70]

def cc_from_phone(ph):
    p = re.sub(r'[^\d+]', '', ph or '')
    for pref, c in sorted(PHONE_CC, key=lambda x: -len(x[0])):
        if p.startswith(pref): return c
    return ''

def cc_from_tld(dom):
    tl = dom.rsplit('.', 1)[-1]
    if dom.endswith('.co.uk') or dom.endswith('.org.uk'): return 'UK'
    for suf, c in (('.com.tr','Turkey'),('.com.mt','Malta'),('.com.au','Australia'),('.co.nz','New Zealand'),
                   ('.co.in','India'),('.net.in','India'),('.com.sg','Singapore'),('.com.cy','Cyprus'),
                   ('.com.gr','Greece'),('.com.hr','Croatia'),('.com.br','Brazil'),('.co.za','South Africa'),
                   ('.com.ua','Ukraine'),('.com.pt','Portugal'),('.com.es','Spain'),('.com.cn','China'),
                   ('.co.jp','Japan'),('.co.kr','South Korea'),('.com.ph','Philippines'),('.com.my','Malaysia'),
                   ('.com.pk','Pakistan'),('.com.eg','Egypt'),('.com.sa','Saudi Arabia'),('.com.ng','Nigeria'),
                   ('.com.lb','Lebanon'),('.com.mx','Mexico'),('.com.ar','Argentina'),('.net.ae','UAE'),('.co.ae','UAE')):
        if dom.endswith(suf): return c
    return TLD_COUNTRY.get(tl, '')

def cc_from_ctx(ctx):
    low = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ ]', ' ', (ctx or '').lower())
    hits = collections.Counter()
    for k, v in COUNTRIES.items():
        n = len(re.findall(r'(?:^|\W)' + re.escape(k) + r'(?:$|\W)', low))
        if n: hits[v] += n
    return hits.most_common(1)[0][0] if hits else ''

ROLE_ORDER = {'Broker':'Broker','Owner (armatör)':'Owner','Owner + Broker':'Broker','Operatör / ship manager':'Manager',
              'Acente (agency)':'Agency'}

out = []
for c in comps:
    dom = c['domain']; s = site.get(dom, {})
    status = s.get('status') or 0
    found = list(s.get('emails_found', []))
    title = s.get('title', '') or ''
    live = 200 <= status < 400
    spam = bool(live and SPAM.search(title))
    parked = bool(live and (PARKED.search(title) or status == 202)) or spam
    reason = s.get('reason', '') or s.get('err', '')

    # ---- name ----
    docname = clean_name(re.sub(r'&[#a-zA-Z0-9]{2,6};?', ' ', _html.unescape(c['name'])))
    docname = re.sub(r'^(?:[a-zçğıöşü]{1,6}\s+)?(?:ine ait|ait|olan|ve|ile|için|adlı)\s+', '', docname, flags=re.I).strip()
    tname = '' if spam else title_name(title)
    b = base(dom)
    cands = []
    for n, src in ((docname, 'doc'), (tname, 'title')):
        if not n or len(n) < 3: continue
        sc = 0.0
        if b and b in norm(n): sc += 5
        elif b and len(b) > 5 and b[:6] in norm(n): sc += 3
        if re.search(r'(Ltd|Limited|S\.?r\.?l|S\.?p\.?A|B\.?V|GmbH|A/S|ApS|\bAB\b|\bAS\b|\bOy\b|O[UÜ]|Inc|LLC|Corp|Group|Shipping|Shipbrok|Brokers?|Chartering|Marine|Maritime|Yacht|Marina|Agency|Agents|Shipyard|Werft|Rederi|Navigation|Bunker|Supplies)', n, re.I): sc += 2
        if GENERIC_NAME.match(n): sc -= 3
        if GEO_TR.search(n): sc -= 4
        if len(n) < 8: sc -= 1.5
        if src == 'doc': sc += 1.0
        if re.search(r'(Home|Welcome|Anasayfa|Benvenuti|Accueil|Startseite|404|Hosting|Domain|Redirecting|Just a moment|Attention Required|Access denied|Error|Untitled|Forbidden|Bir Hata|Site Ba)', n, re.I): sc -= 6
        cands.append((sc, n))
    cands.sort(reverse=True)
    if cands and cands[0][0] > -1:
        name = cands[0][1]
    elif c['kind'] == 'free':
        name = docname or '(firma adı belirsiz)'
    else:
        name = fallback_name(dom)
    if len(name) < 4:
        name = (docname if c['kind'] == 'free' and docname else fallback_name(dom))
    if c['kind'] == 'free' and norm(name) in ('gmail','hotmail','yahoo','outlook','sify','vsnl','rediffmail','aol','icloud','live','msn','mailru','protonmail','libero','web','gmx','netvigator','fastmail','qq','163','126'):
        name = docname if len(docname) > 3 else '(firma adı belirsiz)'

    # ---- country ----
    country = cc_from_tld(dom) or cc_from_phone(c['phone']) or c['country'] or cc_from_ctx(c['ctx']) or ''
    if country == 'USA/Canada': country = 'USA / Canada'
    if country == 'Russia/KZ': country = 'Russia / KZ'

    ctx = c['ctx'] + ' ' + name
    hits = classify2(ctx, name, title)
    role = owner_or_broker(hits, ctx)
    lead = ROLE_ORDER.get(role)
    if lead and lead in hits:
        hits = [lead] + [h for h in hits if h != lead]
    act = activity(hits, name)
    if role == 'Belirsiz': role = 'Belirlenemedi'

    web = ('https://%s/' % dom) if c['kind'] == 'dom' else ''
    if live and not parked and s.get('site'): web = s['site']

    if c['kind'] == 'free':
        websitu = 'Kurumsal site yok (ücretsiz e-posta adresi)'
    elif spam:
        websitu = 'Alan adı el değiştirmiş (alakasız/spam içerik) – firma sitesi değil'
    elif parked:
        websitu = 'Alan adı park/satılık – aktif site yok'
    elif live:
        websitu = 'VAR – site aktif (HTTP %d)' % status
    elif reason == 'ssl':
        websitu = 'Alan adı var ama SSL hatası – site açılmıyor'
    else:
        websitu = 'YOK – alan adı/site yanıt vermiyor'

    doc_emails = c['emails']
    verified = [e for e in doc_emails if e in found]
    dom_on_site = [f for f in found if f.split('@')[-1] == dom]
    partial = [e for e in doc_emails if e not in verified and dom_on_site]
    if c['kind'] == 'free':
        ver = 'Doğrulanamadı – ücretsiz e-posta, kurumsal site yok'
    elif verified:
        ver = 'DOĞRULANDI – adres sitede birebir bulundu'
    elif partial:
        ver = 'KISMİ – site aktif, aynı alan adında e-posta var ama bu adres görünmüyor'
    elif live and not parked:
        ver = 'BELİRSİZ – site aktif, taranan sayfalarda e-posta yok'
    else:
        ver = 'DOĞRULANAMADI – site/alan adı yanıt vermiyor'

    name = re.sub(r'\s+', ' ', re.sub(r'&[#a-zA-Z0-9]{2,6};?', ' ', _html.unescape(name))).strip(' -–—:,./|*')
    weak = (len(name) < 4 or re.match(r'^[a-zçğıöşü]', name) or re.search(r'(<|>|xml|w:t|href|http)', name, re.I)
            or re.match(r'^[a-z0-9.\-]+\.(com|net|org|info|biz|[a-z]{2})$', name, re.I)
            or len(name.split()) > 9)
    if weak:
        name = fallback_name(dom) if c['kind'] == 'dom' else '(firma adı belirsiz)'
    out.append({
        'Firma': name, 'Ülke': country, 'Owner / Broker': role, 'Ne iş yapıyor (kısa)': act,
        'Web sitesi var mı': 'VAR' if (live and not parked) else ('PARK' if parked else 'YOK'),
        'Web sitesi': web, 'Web sitesi durumu': websitu, 'Site başlığı': title,
        'Dokümandaki e-posta(lar)': ', '.join(doc_emails),
        'E-posta doğrulama': ver,
        'Sitede birebir bulunan': ', '.join(verified),
        'Sitede bulunan diğer e-postalar': ', '.join([f for f in found if f not in verified][:8]),
        'Telefon': c['phone'], 'Alan adı': dom,
        '_kind': c['kind'], '_live': bool(live and not parked), '_parked': parked, '_spam': spam,
        '_ver': bool(verified), '_partial': bool(partial), '_emails': doc_emails, '_found': found,
    })

out.sort(key=lambda r: ((r['Ülke'] or 'ZZZ'), r['Firma'].lower()))
json.dump(out, open('work/final.json', 'w'), ensure_ascii=False)
print('rows', len(out), '| site VAR', sum(1 for r in out if r['_live']), '| park', sum(1 for r in out if r['_parked']),
      '| verified', sum(1 for r in out if r['_ver']), '| partial', sum(1 for r in out if r['_partial']))
print(collections.Counter(r['Owner / Broker'] for r in out).most_common(8))
print(collections.Counter(r['Ülke'] for r in out).most_common(12))
