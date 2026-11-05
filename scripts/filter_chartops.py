import json, re, sys, collections, html as _html
sys.path.insert(0, 'work')
from classify import clean_name, fallback_name, classify, classify2, owner_or_broker, activity
from fixdom import fix
from parse import TLD_COUNTRY, PHONE_CC, COUNTRIES

# ---- per-email records (all phones kept, no domain merging) ----
recs = json.load(open('work/records.json'))
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'\+\d[\d\s\-\./\(\)]{5,}\d')
EMOJI = re.compile(r'[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿️⃣]')
sys.path.insert(0, 'work')
import importlib.util
spec = importlib.util.spec_from_file_location('ex', 'work/extract3.py')

# reuse the name picker from extract3 by importing its functions
src = open('work/extract3.py').read()
ns = {}
exec(src[:src.rindex('out = []')], ns)
pick = ns['pick']

rows = []
for r in recs:
    s = r['raw']
    ms = list(EMAIL_RE.finditer(s))
    prev_end, last_name = 0, ''
    for i, m in enumerate(ms):
        chunk = s[prev_end:m.start()]
        name = pick(chunk)
        if len(name) < 4:
            name = last_name or pick(s[:m.start()])
        else:
            last_name = name
        nxt = ms[i + 1].start() if i + 1 < len(ms) else len(s)
        after = s[m.end():nxt]
        before = s[prev_end:m.start()]
        ph = [p.strip(' .,;') for p in PHONE_RE.findall(after)]
        if not ph:
            ph = [p.strip(' .,;') for p in PHONE_RE.findall(before)]
        if not ph:
            near = [(min(abs(pm.start() - m.end()), abs(m.start() - pm.end())), pm.group(0).strip(' .,;'))
                    for pm in PHONE_RE.finditer(s)]
            near = [x for x in near if x[0] <= 260]
            near.sort()
            ph = [near[0][1]] if near else []
        lp, d = m.group(0).strip('.,;').lower().rsplit('@', 1)
        d, _junk = fix(d)
        rows.append({'email': lp + '@' + d, 'local': lp, 'domain': d, 'company_raw': name,
                     'phones': list(dict.fromkeys(ph))[:4], 'country_line': r['country'],
                     'ctx': re.sub(r'\s+', ' ', EMOJI.sub(' ', s[:220] + ' ' + s[max(0, prev_end - 80):nxt]))[:900],
                     'raw_snip': re.sub(r'\s+', ' ', EMOJI.sub(' ', s[max(0, prev_end - 40):nxt]))[:400]})
        prev_end = m.end()

# dedupe identical email+phones
seen, ded = set(), []
for r in rows:
    k = (r['email'], tuple(r['phones']))
    if k in seen: continue
    seen.add(k); ded.append(r)
rows = ded
print('e-posta kaydı (tekilleştirilmiş):', len(rows))

# ---- site data ----
site = {}
for fn in ('work/checked.jsonl', 'work/retry.jsonl', 'work/checked2.jsonl'):
    for l in open(fn):
        x = json.loads(l); d = x['domain']
        prev = site.get(d)
        if prev is None or ((x.get('status') or 0) > 0 and (prev.get('status') or 0) == 0):
            site[d] = x

# ---- filters ----
YACHT = re.compile(r'(yacht|yat\b|yat[çc]|yachting|superyacht|megayacht|marina|berth|bağlama|sail(ing|boat)?\b|boat|tekne|gulet|catamaran|katamaran|motoryat|yelkenli|cruis(e|ing)|crocier|crociere|charter brokerage|yat kiralama|pleasure craft|leisure|resort|tourism|turizm|seyahat|travel)', re.I)
KEEP_ROLE = {'Owner (armatör)', 'Owner + Broker', 'Broker', 'Operatör / ship manager'}
STRICT_LOCAL = re.compile(r'^(chartering|charter|charters|chart|ops|operation|operations|operasyon|oper|dryops|dryoper|drycargo|commercial|comm|fleet|snp|s&p|owner|owners|armador|post ?fixture|postfix|voyage|broker|brokers|brokerage|shipbroking)([._\-]?[a-z0-9]{0,12})?$', re.I)
KEEP_LOCAL = re.compile(r'^(chartering|charter|charters|chart|ops|operation|operations|operasyon|oper|dryops|dryoper|drycargo|dry|commercial|comm|fleet|snp|s&p|sp|owner|owners|armador|post ?fixture|postfix|bulk|tanker|cargo|freight|voyage|broker|brokers|brokerage|shipbroking)([._\-]?[a-z0-9]{0,12})?$', re.I)
OFFSECTOR = re.compile(r'^(Ship chandler|Lojistik|Deniz sigortası|Crewing|Dernek|Danışmanlık|Marina|Teknik servis)', re.I)
KEEP_CTX = re.compile(r'(chartering|charter desk|shipbrok|ship brok|dry cargo|dry bulk|bulk carrier|tanker|voyage|time charter|s&p|sale\s*(&|and)\s*purchase|shipowner|ship owner|armat[öo]r|gemi sahibi|rederi|reederei|armateur|fleet operat|vessel operat|commercial operat|operations manager|post ?fixture|chartering manager)', re.I)

def cc_from_phone(ph):
    p = re.sub(r'[^\d+]', '', ph or '')
    for pref, c in sorted(PHONE_CC, key=lambda x: -len(x[0])):
        if p.startswith(pref): return c
    return ''

def cc_from_tld(dom):
    if dom.endswith(('.co.uk', '.org.uk')): return 'UK'
    for suf, c in (('.com.tr','Turkey'),('.com.mt','Malta'),('.com.au','Australia'),('.co.nz','New Zealand'),
                   ('.co.in','India'),('.net.in','India'),('.com.sg','Singapore'),('.com.cy','Cyprus'),
                   ('.com.gr','Greece'),('.com.hr','Croatia'),('.com.br','Brazil'),('.co.za','South Africa'),
                   ('.com.ua','Ukraine'),('.com.pt','Portugal'),('.com.es','Spain'),('.com.cn','China'),
                   ('.co.jp','Japan'),('.co.kr','South Korea'),('.com.ph','Philippines'),('.com.my','Malaysia'),
                   ('.com.pk','Pakistan'),('.com.eg','Egypt'),('.com.sa','Saudi Arabia'),('.com.ng','Nigeria'),
                   ('.com.lb','Lebanon'),('.com.mx','Mexico'),('.com.ar','Argentina'),('.net.ae','UAE'),('.co.ae','UAE')):
        if dom.endswith(suf): return c
    return TLD_COUNTRY.get(dom.rsplit('.', 1)[-1], '')

def cc_from_ctx(ctx):
    low = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ ]', ' ', (ctx or '').lower())
    h = collections.Counter()
    for k, v in COUNTRIES.items():
        n = len(re.findall(r'(?:^|\W)' + re.escape(k) + r'(?:$|\W)', low))
        if n: h[v] += n
    return h.most_common(1)[0][0] if h else ''

FREE = set('''gmail.com googlemail.com hotmail.com hotmail.co.uk hotmail.it hotmail.fr hotmail.gr outlook.com
outlook.it live.com yahoo.com yahoo.co.uk yahoo.gr yahoo.it yahoo.in yahoo.co.in rediffmail.com aol.com
icloud.com me.com gmx.de gmx.net web.de mail.ru yandex.ru protonmail.com proton.me libero.it alice.it
virgilio.it tiscali.it tin.it fastwebnet.it wanadoo.fr orange.fr free.fr sfr.fr laposte.net vsnl.net
vsnl.com vsnl.net.in md5.vsnl.net.in bsnl.in sify.com airtelmail.in netvigator.com fastmail.fm mailbox.org
bluewin.ch telenet.be skynet.be ziggo.nl planet.nl kpnmail.nl online.no telia.com telia.se bredband.net
comhem.se mail.dk post.dk hotmail.dk mail.ee hot.ee otenet.gr forthnet.gr in.gr mail.gr windowslive.com
msn.com qq.com 163.com 126.com 263.net sina.com naver.com daum.net hanmail.net emirates.net.ae eim.ae
etisalat.ae zonnet.nl terra.com seznam.cz op.pl wp.pl o2.pl interia.pl onet.pl abv.bg mail.bg t-online.de
arcor.de freenet.de ocn.ne.jp usa.net'''.split())

SPAM = re.compile(r'(casino|bahis|betting|slot|poker|porn|escort|viagra|loan|crypto|essay|replica|gambling|jackpot|pharmacy)', re.I)
PARKED = re.compile(r'(domain (is )?for sale|buy this domain|parked|domain name|under construction|coming soon|website expired|sedo\b|godaddy|namecheap|default web site|apache2 (ubuntu|debian)|index of /|account suspended|site not found|plesk|cpanel|web hosting)', re.I)

GENERIC_NAME = re.compile(r'^(ltd|limited|shipbroker|shipbrokers?|broker|brokers|brokerage|chartering|shipping|marine|maritime|agency|agents?|office|sales|contact|info|group|company|co|services?|solutions?|bu |ve |the )\\b', re.I)
GEO_TR = re.compile(r'(brezilya|latin amerika|avrupa|asya|afrika|orta doğu|uzak doğu|akdeniz|karadeniz|baltık|kuzey|güney|bölgesi|yeni eklenen|liste|kişi bazlı|temaslar|firmalar|ek kişiler|diğer|endonezya|kanada|singapur|hindistan|çin)', re.I)

def _norm(x): return re.sub(r'[^a-z0-9]', '', (x or '').lower())

def _base(dom):
    p = dom.split('.')
    b = p[-3] if (len(p) >= 3 and len(p[-2]) <= 3) else (p[-2] if len(p) >= 2 else p[0])
    return re.sub(r'[^a-z0-9]', '', b.lower())

def _title_name(title):
    if not title: return ''
    t = [x.strip() for x in re.split(r'\s*[\|\u2013\u2014\-\u00b7:;\u00bb\u2022]\s*|\s{2,}', title) if len(x.strip()) >= 3]
    if not t: return ''
    t.sort(key=lambda x: (-1 if re.search(r'(Ltd|S\.?r\.?l|S\.?p\.?A|B\.?V|GmbH|A/S|ApS|\bAB\b|\bAS\b|Inc|LLC|Group|Shipping|Marine|Maritime|Brokers?|Chartering|Agency)', x, re.I) else 0, len(x)))
    return t[0][:70]

def best_name(docname, title, dom, isfree):
    b = _base(dom)
    cands = []
    for n, src in ((docname, 'doc'), (_title_name(title), 'title')):
        if not n or len(n) < 3: continue
        sc = 0.0
        if b and b in _norm(n): sc += 5
        elif b and len(b) > 5 and b[:6] in _norm(n): sc += 3
        if re.search(r'(Ltd|Limited|S\.?r\.?l|S\.?p\.?A|B\.?V|GmbH|A/S|ApS|\bAB\b|\bAS\b|\bOy\b|O[UÜ]|Inc|LLC|Corp|Group|Shipping|Shipbrok|Brokers?|Chartering|Marine|Maritime|Agency|Rederi|Navigation|Tanker|Bulk|d\.o\.o|d\.d)', n, re.I): sc += 2
        if GENERIC_NAME.match(n): sc -= 3
        if GEO_TR.search(n): sc -= 4
        if re.match(r'^[a-zçğıöşü]', n): sc -= 4
        if re.match(r'^[a-z0-9.\-]+\.(com|net|org|info|biz|[a-z]{2})$', n.strip(), re.I): sc -= 6
        if re.search(r'(Home|Welcome|Anasayfa|Accueil|Startseite|404|Hosting|Domain|Redirecting|Just a moment|Attention Required|Access denied|Error|Untitled|Forbidden)', n, re.I): sc -= 6
        if len(n) < 8: sc -= 1.5
        if src == 'doc': sc += 1.0
        cands.append((sc, n))
    cands.sort(reverse=True)
    if cands and cands[0][0] > -1: return cands[0][1]
    return fallback_name(dom) if not isfree else (docname or '(firma adı belirsiz)')

out, dropped_yacht, dropped_role = [], 0, 0
for r in rows:
    dom = r['domain']; s = site.get(dom, {})
    status = s.get('status') or 0; title = s.get('title', '') or ''
    found = list(s.get('emails_found', []))
    live = 200 <= status < 400
    spam = bool(live and SPAM.search(title))
    parked = bool(live and (PARKED.search(title) or status == 202)) or spam
    name = clean_name(re.sub(r'&[#a-zA-Z0-9]{2,6};?', ' ', _html.unescape(r['company_raw'])))
    blob = ' '.join([name, dom, r['raw_snip'], '' if spam else title])
    if YACHT.search(blob):
        dropped_yacht += 1; continue
    hits = classify2(r['ctx'] + ' ' + name, name, '' if spam else title)
    role = owner_or_broker(hits, r['ctx'] + ' ' + name)
    CH = re.compile(r'(^|[._\-])(chartering|charter|charters|chart|fixture|fixtures|postfix|postfixture|voyage|dryops|dryoper|drycargo|drybulk|bulkchartering|tankerchartering|chartering1|chrt)([._\-0-9]|$)', re.I)
    OP = re.compile(r'(^|[._\-])(ops|op|oper|opr|operation|operations|operasyon|operations1|marineops|portops|shipops|vesselops|fleetops|opsdesk)([._\-0-9]|$)', re.I)
    is_ch, is_op = bool(CH.search(r['local'])), bool(OP.search(r['local']))
    keep = is_ch or is_op
    if not keep:
        dropped_role += 1; continue
    mailtype = 'Chartering + Operation' if (is_ch and is_op) else ('Chartering' if is_ch else 'Operation')
    name = best_name(name, '' if spam else title, dom, dom in FREE)
    name = re.sub(r'\s+', ' ', re.sub(r'&[#a-zA-Z0-9]{2,6};?', ' ', _html.unescape(name))).strip(' -–—:,./|*')
    if len(name) < 4 or re.match(r'^[a-zçğıöşü]', name) or re.search(r'(<|>|xml|w:t|href|http)', name, re.I) \
       or re.match(r'^[a-z0-9.\-]+\.(com|net|org|info|biz|[a-z]{2})$', name, re.I) or len(name.split()) > 9:
        name = fallback_name(dom) if dom not in FREE else '(firma adı belirsiz)'
    lead = {'Broker': 'Broker', 'Owner (armatör)': 'Owner', 'Owner + Broker': 'Broker',
            'Operatör / ship manager': 'Manager'}.get(role)
    if lead and lead in hits: hits = [lead] + [h for h in hits if h != lead]
    act = activity(hits, name)
    act = (act.replace('Gemi/yat brokerliği', 'Gemi brokerliği')
              .replace('Tersane / refit, bakım-onarım, dry dock, yat inşa', 'Tersane / gemi bakım-onarım, dry dock')
              .replace('Gemi & yat işletme / filo yönetimi', 'Gemi işletme / filo yönetimi'))
    country = cc_from_tld(dom) or cc_from_phone(r['phones'][0] if r['phones'] else '') or r['country_line'] or cc_from_ctx(r['ctx'])
    if country in ('USA/Canada', 'Russia/KZ'): country = country.replace('/', ' / ')
    isfree = dom in FREE
    if isfree: websitu, web = 'Kurumsal site yok (ücretsiz e-posta)', ''
    elif spam: websitu, web = 'Alan adı el değiştirmiş (alakasız içerik)', 'https://%s/' % dom
    elif parked: websitu, web = 'Alan adı park/satılık – aktif site yok', 'https://%s/' % dom
    elif live: websitu, web = 'VAR – site aktif (HTTP %d)' % status, (s.get('site') or 'https://%s/' % dom)
    elif s.get('reason') == 'ssl': websitu, web = 'Alan adı var, SSL hatası', 'https://%s/' % dom
    else: websitu, web = 'YOK – alan adı/site yanıt vermiyor', 'https://%s/' % dom
    verified = r['email'] in found
    dom_mails = [f for f in found if f.split('@')[-1] == dom]
    if isfree: ver, st = 'Doğrulanamadı – ücretsiz e-posta', 'bad'
    elif verified: ver, st = 'DOĞRULANDI – adres sitede birebir bulundu', 'ok'
    elif dom_mails: ver, st = 'KISMİ – site aktif, aynı alan adında e-posta var', 'part'
    elif live and not parked: ver, st = 'BELİRSİZ – site aktif, sayfalarda e-posta yok', 'unk'
    else: ver, st = 'DOĞRULANAMADI – site/alan adı yanıt vermiyor', 'bad'
    out.append({'Firma': name, 'Ülke': country, 'Mail tipi': mailtype, 'Rol (sektördeki konumu)': role,
                'Sektör / ne iş yapıyor': act, 'E-posta': r['email'], 'Departman (mail eki)': r['local'],
                'Telefon(lar)': ' / '.join(r['phones']), 'Web sitesi': web, 'Web sitesi durumu': websitu,
                'E-posta doğrulama': ver, 'Sitede bulunan diğer e-postalar': ', '.join(dom_mails[:6]),
                'Site başlığı': '' if spam else title, 'Alan adı': dom,
                'Kaynak metin (dokümandan)': r['raw_snip'],
                '_st': st, '_live': bool(live and not parked), '_role': role, '_mt': mailtype,
                '_phones': r['phones']})

out.sort(key=lambda x: (x['Ülke'] or 'ZZZ', x['Firma'].lower(), x['E-posta']))
json.dump(out, open('work/chartops.json', 'w'), ensure_ascii=False)
print('yat ile ilgili silinen:', dropped_yacht, '| owner/chartering/operation dışı silinen:', dropped_role)
print('KALAN e-posta kaydı:', len(out), '| firma(alan adı):', len({x['Alan adı'] for x in out}))
print(collections.Counter(x['_mt'] for x in out).most_common())
print(collections.Counter(x['_role'] for x in out).most_common())
print(collections.Counter(x['_st'] for x in out).most_common())
