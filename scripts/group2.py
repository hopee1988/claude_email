import re, json, collections
rows = json.load(open('work/emails2.json'))
FREE = set('''gmail.com googlemail.com hotmail.com hotmail.co.uk hotmail.it hotmail.fr hotmail.gr outlook.com
outlook.it live.com yahoo.com yahoo.co.uk yahoo.gr yahoo.it yahoo.in yahoo.co.in rediffmail.com aol.com
icloud.com me.com gmx.de gmx.net web.de mail.ru yandex.ru protonmail.com proton.me libero.it alice.it
virgilio.it tiscali.it tin.it pec.it fastwebnet.it wanadoo.fr orange.fr free.fr sfr.fr laposte.net
vsnl.net vsnl.com vsnl.net.in md5.vsnl.net.in bsnl.in sify.com airtelmail.in netvigator.com
fastmail.fm mailbox.org bluewin.ch telenet.be skynet.be ziggo.nl planet.nl kpnmail.nl online.no
telia.com telia.se bredband.net comhem.se mail.dk post.dk hotmail.dk mail.ee hot.ee neti.ee
otenet.gr ath.forthnet.gr forthnet.gr in.gr mail.gr windowslive.com msn.com qq.com 163.com 126.com
sina.com naver.com daum.net hanmail.net emirates.net.ae eim.ae etisalat.ae zonnet.nl terra.com
seznam.cz op.pl wp.pl o2.pl interia.pl onet.pl abv.bg mail.bg t-online.de arcor.de freenet.de'''.split())

by = collections.defaultdict(lambda: {'emails': [], 'names': [], 'countries': [], 'phones': [], 'urls': [], 'ctx': []})
singles = []
SUFFIX = re.compile(r'(Ltd|Limited|LLC|S\.?r\.?l|S\.?p\.?A|SARL|SAS|S\.A|B\.?V|N\.?V|GmbH|A/S|ApS|\bAB\b|\bAS\b|\bOy\b|\bOU\b|OÜ|Inc|Corp|Co\.|Group|Shipping|Shipbrok|Brokers?|Brokerage|Chartering|Marine|Maritime|Yacht|Marina|Agency|Agents|Tanker|Bulk|Logistics|Suppliers?|Chandler|Shipyard|Werft|Rederi|Navigation|Lines?|Services|Management|Bunker)', re.I)

def key(e):
    d = e.split('@')[1]
    return d

for r in rows:
    d = key(r['email'])
    g = by[('free', r['email']) if d in FREE else ('dom', d)]
    g['emails'].append(r['email']); g['names'].append(r['company'])
    if r['country']: g['countries'].append(r['country'])
    if r['phone']: g['phones'].append(r['phone'])
    if r['url_given']: g['urls'].append(r['url_given'])
    g['ctx'].append(r['ctx'])

def best_name(names, dom):
    cnt = collections.Counter(n for n in names if len(n) >= 4)
    scored = []
    for n, c in cnt.items():
        sc = c * 0.5
        if SUFFIX.search(n): sc += 3
        base = dom.split('.')[0].replace('-', '')
        if base and base.lower() in re.sub(r'[^a-z]', '', n.lower()): sc += 4
        if re.search(r'[ÇĞİÖŞÜçğıöşü]', n) and not re.search(r'(Türk|Turk|Istanbul|İstanbul|Izmir|İzmir|Mersin|Ltd|A\.Ş)', n): sc -= 1
        if len(n) > 60: sc -= 2
        if re.match(r'^[a-z0-9.\-]+\.(com|net|org|[a-z]{2})$', n.strip()): sc -= 3
        scored.append((sc, n))
    if not scored: return names[0] if names else ''
    scored.sort(reverse=True)
    return scored[0][1]

comps = []
for (kind, k), g in by.items():
    dom = k if kind == 'dom' else k.split('@')[1]
    name = best_name(g['names'], dom)
    name = re.sub(r'\s+', ' ', name).strip(' :,-–—.|/')
    comps.append({'kind': kind, 'domain': dom, 'name': name,
                  'emails': sorted(set(g['emails'])),
                  'country': collections.Counter(g['countries']).most_common(1)[0][0] if g['countries'] else '',
                  'phone': g['phones'][0] if g['phones'] else '',
                  'url_given': g['urls'][0] if g['urls'] else '',
                  'ctx': ' ||| '.join(dict.fromkeys(g['ctx']))[:2000]})
print('companies/groups:', len(comps), 'corporate domains:', sum(1 for c in comps if c['kind']=='dom'), 'freemail rows:', sum(1 for c in comps if c['kind']=='free'))
json.dump(comps, open('work/companies2.json','w'), ensure_ascii=False)
for c in comps[:5]: print(c['domain'],'|',c['name'],'|',len(c['emails']))
