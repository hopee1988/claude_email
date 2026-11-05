import re, json

STOP = r'(?:Danimarka|Danimarkalı|İsveç|Isveç|Norveç|Finlandiya|Hollanda|Almanya|Fransa|İtalya|Italya|İspanya|Portekiz|Yunanistan|Türkiye|Hindistan|Birleşik Krallık|İngiltere|Malta|Singapur|Kıbrıs|Hırvatistan|Bulgaristan|Karadağ|Estonya|Letonya|Litvanya|Polonya|Romanya|Ukrayna|Rusya|merkezli|merkezi|bazlı|ve çevresi|dünya çapında|Deniz yakıtı|Uluslararası|Profesyonel|Şirket|Firma|Adres|Telefon|Görev|Alan|Bölge|Hizmet|Faaliyet|Konum|genel|Genel)'

def clean_name(n):
    n = re.sub(r'\s+', ' ', n or '').strip()
    n = re.sub(r'([a-zçğıöşü\)\.])([A-ZÇĞİÖŞÜ])', r'\1 \2', n)        # glued words
    n = re.sub(r'\s*[\(\[]?\s*' + STOP + r'.*$', '', n)                # cut descriptive tail
    # repair over-eager camel splits
    for a, b2 in (('Gmb H','GmbH'),('S. p. A','S.p.A'),('S. r. l','S.r.l'),('S.r. l','S.r.l'),('S. A','S.A'),
                  ('B. V','B.V'),('N. V','N.V'),('A/ S','A/S'),('Ap S','ApS'),('L. L. C','L.L.C'),('Ltd A','Ltd. A'),
                  ('S. A. S','S.A.S'),('A. Ş','A.Ş'),('Co. Ltd','Co. Ltd'),('P. L. C','PLC'),('d. o. o','d.o.o'),
                  ('d. d','d.d'),('O [UÜ]','OÜ')):
        n = n.replace(a, b2)
    n = re.sub(r'\bGmb\s*H\b','GmbH', n)
    # drop leading ALL-CAPS section headers (e.g. "DRY BULK / S&P BROKERLARI")
    n = re.sub(r'^(?:[A-ZÇĞİÖŞÜ&/\.\- ]{6,}?)(?=[A-ZÇĞİÖŞÜ][a-zçğıöşü])', '', n)
    n = re.sub(r'^\W+|\W+$', '', n)
    n = re.sub(r'\s+', ' ', n).strip(' -–—:,./|')
    if len(n) > 70: n = n[:70].rsplit(' ', 1)[0]
    return n

def fallback_name(dom):
    b = dom.split('.')[0]
    return re.sub(r'[-_]+', ' ', b).title()

RULES = [
 ('Broker',   r'(ship\s*brok|shipbrok|brokerage|broker|courtier|makler|chartering|charter desk|\bs&p\b|sale\s*(&|and)\s*purchase|snp@|chartering@|fixture|affr[eé]t)'),
 ('Owner',    r'(shipowner|ship\s*owner|vessel owner|armat[öo]r|gemi sahibi|rederi|reederei|armateur|shipowning|fleet owner|fleet manag|armament|naviera|navigazione|navigation co|shipping line|liner operator|filo sahibi|own(s|ed|ing) (a )?fleet|own fleet|gemi i̇şletmecisi|gemi isletmecisi|tanker operator|bulk carrier operator|d\.d\. \(|plovidba)'),
 ('Manager',  r'(ship\s*management|shipmanagement|fleet management|technical management|crew management|ism|dpa|yacht management|management ag)'),
 ('Agency',   r'(ship agency|port agent|shipping agency|agenzia marittima|acente|agency|agent services|husbandry)'),
 ('Shipyard', r'(shipyard|tersane|werft|varvet|dry dock|drydock|refit|boatyard|cantiere|astillero|repair yard|newbuild|yacht builder|yat üretici)'),
 ('Supplier', r'(chandler|ship supply|ship stores|provision|kumanya|marine suppl|spare parts|yedek parça|equipment suppl|teknik tedarik|deck & engine|marine store)'),
 ('Marina',   r'(marina|berth|bağlama|yacht harbour|haven|port de plaisance|yacht club)'),
 ('Bunker',   r'(bunker|marine fuel|fuel suppl|yakıt|lubricant|madeni yağ|oil trader)'),
 ('Service',  r'(technical service|teknik servis|survey|class(ification)?|elektronik|mekanik|electrical|automation|maintenance|bakım|onarım|hull clean|diving)'),
 ('Logistics',r'(logistics|forwarding|freight forward|lojistik|nakliye|transport)'),
 ('Insurance',r'(insurance|p&i|sigorta|claims|underwrit|average adjust)'),
 ('Crewing',  r'(crewing|crew agency|manning|personnel|mürettebat|seafarer|academy|training|university|maritime college)'),
 ('Assoc',    r'(association|chamber|derne[kğ]|federa|syndicale|cluster|authority|ministry|institute|council)'),
 ('Charter',  r'(yacht charter|charter company|kiralama|rental|boat rental|cruise|crociere|tour)'),
 ('Consult',  r'(consultan|danışman|advisory|law|hukuk|legal|avukat|accounting|audit)'),
]

ACT = {
 'Broker':   'Gemi/yat brokerliği – chartering & S&P',
 'Owner':    'Armatör / gemi sahibi – filo işletmesi',
 'Manager':  'Gemi & yat işletme / filo yönetimi (ISM, teknik, crew)',
 'Agency':   'Liman acenteliği / gemi acentesi hizmetleri',
 'Shipyard': 'Tersane / refit, bakım-onarım, dry dock, yat inşa',
 'Supplier': 'Ship chandler / kumanya & teknik malzeme tedariki',
 'Marina':   'Marina & bağlama, liman hizmetleri',
 'Bunker':   'Bunker / marine yakıt & madeni yağ tedariki',
 'Service':  'Teknik servis, elektrik-mekanik-elektronik bakım, survey',
 'Logistics':'Lojistik / nakliye & freight forwarding',
 'Insurance':'Deniz sigortası / P&I, hasar & claims',
 'Crewing':  'Crewing / personel tedariki & denizcilik eğitimi',
 'Assoc':    'Dernek / oda / resmi kurum – sektör organizasyonu',
 'Charter':  'Yat kiralama / charter operasyonu',
 'Consult':  'Danışmanlık / hukuk & finans hizmetleri',
}
ROLE_TR = {'Owner': 'Owner (armatör)', 'Broker': 'Broker', 'Manager': 'Operatör / ship manager'}

def classify(text):
    t = text.lower()
    hits = [k for k, p in RULES if re.search(p, t, re.I)]
    return hits

def owner_or_broker(hits, text):
    t = text.lower()
    has_b = 'Broker' in hits
    has_o = 'Owner' in hits
    # avoid false owner from the word "owner/proprietor" of a small supplier firm
    if has_o and re.search(r'(proprietor|owner / director|owner/director|owner & director)', t) and not re.search(r'(shipowner|gemi sahibi|rederi|fleet|vessel owner|armat)', t):
        has_o = False
    if has_b and has_o: return 'Owner + Broker'
    if has_b: return 'Broker'
    if has_o: return 'Owner (armatör)'
    if 'Manager' in hits: return 'Operatör / ship manager'
    if 'Agency' in hits: return 'Acente (agency)'
    for k in ('Shipyard','Supplier','Marina','Bunker','Service','Charter','Logistics','Insurance','Crewing','Assoc','Consult'):
        if k in hits: return 'Diğer – ' + k
    return 'Belirsiz'

NAMEHINT = [
 (r'(shipbrok|brokers?|brokerage|chartering|charter(ing)? ?(ltd|srl|bv|ab|as)?|courtier|maritime brokers)', 'Broker'),
 (r'(shipyard|werft|varvet|cantiere|astillero|tersane|boatyard|refit|yachts?\b.*(build|yard))', 'Shipyard'),
 (r'(marina|yacht ?club|harbour|haven|port authority|liman)', 'Marina'),
 (r'(agency|agencies|agent|agenzia|acente|shipping agency)', 'Agency'),
 (r'(bunker|fuel|oil|petrol|lubric)', 'Bunker'),
 (r'(chandler|suppl|stores|provision|spares|equipment|trading|tedarik)', 'Supplier'),
 (r'(rederi|reederei|navigation|navigazione|naviera|lines|plovidba|shipowners)', 'Owner'),
 (r'(ship ?management|shipmanagement|management|crewing|manning)', 'Manager'),
 (r'(logistic|forwarding|freight|transport|lojistik)', 'Logistics'),
 (r'(insurance|sigorta|underwrit)', 'Insurance'),
 (r'(service|servis|marine tech|engineering|elektronik|refrig|hydraul)', 'Service'),
 (r'(yacht|yat|boat|sail|superyacht|charter)', 'Charter'),
 (r'(association|chamber|federa|derne|institut|academy|university)', 'Assoc'),
]
def classify2(ctx, name, title=''):
    hits = classify(ctx + ' ' + title)
    if not hits:
        blob = (name + ' ' + title).lower()
        for p, k in NAMEHINT:
            if re.search(p, blob, re.I):
                hits = [k]; break
    if not hits:
        blob = (name + ' ' + title + ' ' + ctx).lower()
        if re.search(r'(ship|gemi|marine|maritime|denizcilik|vessel|port|liman|sea|deniz)', blob):
            hits = ['_MARINE']
    return hits

def activity(hits, name):
    pri = ['Broker','Owner','Manager','Shipyard','Supplier','Bunker','Agency','Marina','Service','Charter','Logistics','Insurance','Crewing','Assoc','Consult']
    picks = [h for h in pri if h in hits][:3]
    if hits == ['_MARINE']:
        return 'Genel denizcilik / gemi hizmetleri firması'
    if not picks:
        return 'Denizcilik sektörü firması (ayrıntı belirtilmemiş)'
    return ' | '.join(ACT[p] for p in picks)
