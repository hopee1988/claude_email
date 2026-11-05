import re, json

recs = json.load(open('work/records.json'))
EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'\+\d[\d\s\-\./\(\)]{5,}\d')
URL_RE   = re.compile(r'(?:https?://|www\.)[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)+(?:/[^\s,;]*)?', re.I)
EMOJI    = re.compile(r'[\U0001F000-\U0001FAFF←-⇿⌀-➿⬀-⯿️⃣™®•]')
LABELS = r'(?:Genel\s+e-?posta|Alternatif\s+e-?postalar|E-?post[ae]|E-?mail|Email|Mail|Telefon|Phone|Mobile|Mob|Tel|Fax|Adres|Address|Web(?:site)?|Görev|Alan|Bölge|Firma|Hizmet|Faaliyet|Konum|Rol|Yetkili|Ofis|Office|Kişi|Contact|İletişim|WhatsApp|Direct|Merkez|Not|Açıklama|Segment|Kategori|Uzmanlık|Pozisyon|Şirket(?:\s+adı)?|numarası)'
SUFFIX = re.compile(r'(Ltd|Limited|LLC|L\.L\.C|S\.?r\.?l|S\.?p\.?A|SARL|SAS|S\.A|BV|B\.V|NV|N\.V|GmbH|A/S|ApS|\bAB\b|\bAS\b|\bOy\b|\bOU\b|OÜ|Inc|Corp|Co\.|Group|Holding|Shipping|Shipbrok|Brokers?|Brokerage|Chartering|Marine|Maritime|Yacht|Marina|Agency|Agencies|Agents|Tanker|Bulk|Logistics|Supplies|Suppliers|Chandler|Shipyard|Werft|Varvet|Rederi|Navigation|Lines?|Services|Management|Bunker)', re.I)
ADDRHINT = re.compile(r'(\d{4,6}|Street|\bStr\b|Via |Viale|Road|\bRd\b|Avenue|\bAve\b|Blvd|Boulevard|Quai|Rue |Calle |Strada|Gata|Gatan|Vej|Weg|Chaussee|Floor|Suite|P\.?O\.? Box|Mah\.|Cad\.|Sok\.|No[\.:]?\s*\d)', re.I)

def cands(chunk):
    s = EMOJI.sub(' ', chunk)
    s = re.sub(r'\(?\+\d[\d\s\-\./\(\)]{5,}\d\)?', ' | ', s)
    s = URL_RE.sub(' | ', s)
    s = re.sub(LABELS + r'\s*[:\-–]?\s*', ' | ', s, flags=re.I)
    s = re.sub(r'\s+', ' ', s)
    out = []
    for p in re.split(r'\|', s):
        for q in re.split(r'[,;]|\s–\s|\s-\s', p):
            q = re.sub(r'^\d{1,3}[\)\.\-]\s*', '', q).strip(' :,-–—.|/​')
            if len(q) >= 3: out.append(q)
    return out

def pick(chunk):
    cs = cands(chunk)
    if not cs: return ''
    best, bestscore = '', -99
    for i, c in enumerate(cs):
        sc = 0.0
        if SUFFIX.search(c): sc += 4
        if ADDRHINT.search(c): sc -= 4
        if re.match(r'^[a-zçğıöşü]', c): sc -= 1.5
        if len(c) > 70: sc -= 2
        if len(c) < 6: sc -= 1
        sc -= i * 0.6
        if sc > bestscore: best, bestscore = c, sc
    if len(best) > 80: best = best[:80].rsplit(' ',1)[0]
    return best.strip(' :,-–—.|/')

out = []
for r in recs:
    s = r['raw']; country = r['country']
    ms = list(EMAIL_RE.finditer(s))
    prev_end, last_name = 0, ''
    for i, m in enumerate(ms):
        chunk = s[prev_end:m.start()]
        name = pick(chunk)
        if len(name) < 4:
            name = last_name or pick(s[:m.start()])
        else:
            last_name = name
        nxt = ms[i+1].start() if i+1 < len(ms) else len(s)
        ctx = s[max(0, prev_end-80):nxt]
        phones = PHONE_RE.findall(ctx)
        urls = URL_RE.findall(ctx)
        out.append({'email': m.group(0).strip('.,;').lower(), 'company': name, 'country': country,
                    'phone': phones[0].strip() if phones else '',
                    'url_given': (urls[0] if urls else ''),
                    'ctx': re.sub(r'\s+',' ', EMOJI.sub(' ', s[:220] + ' ' + ctx))[:900]})
        prev_end = m.end()

json.dump(out, open('work/emails.json','w'), ensure_ascii=False)
print('rows', len(out), 'weak', sum(1 for o in out if len(o['company'])<4))
for o in out[:3]+out[498:506]+out[1500:1504]: print(repr(o['company']),'|',o['email'])
