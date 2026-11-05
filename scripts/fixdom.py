import json, re
TLD2 = ['co.uk','org.uk','me.uk','ac.uk','com.tr','org.tr','net.tr','gov.tr','com.mt','org.mt','net.mt',
 'com.au','net.au','org.au','co.nz','net.nz','com.sg','com.my','co.in','net.in','org.in','co.za','com.br',
 'com.cy','com.gr','com.hr','com.ua','com.pl','co.il','com.eg','com.sa','com.ar','com.mx','com.hk','com.cn',
 'co.jp','co.kr','com.ph','co.th','com.vn','com.pt','com.es','com.it','com.de','com.gi','net.gi','com.ng',
 'com.pk','com.bd','com.lk','net.ae','co.ae','com.qa','com.om','com.kw','com.bh','com.lb','com.jo','com.tn',
 'com.ru','net.ru','org.ru','com.ee','net.nl']
TLD1 = ('com net org info biz edu gov coop aero travel name pro mobi asia tel xyz online site shop group global '
 'world email services solutions company team life club live digital app dev cloud io ai me tv cc gi mt gr it fr '
 'es pt nl be de ch at dk se no fi ee lv lt pl cz sk hu ro bg hr si rs ua ru tr uk ie is mc lu cy il ae qa sa om '
 'kw bh in pk lk bd cn hk tw jp kr sg my th vn id ph au nz za ng ke gh ma tn dz eg br ar cl pe co mx us ca pa lr '
 'mh ky vg bs bm jm fm ltd eu yachts marine boats agency navy').split()
ALT = '|'.join([re.escape(t) for t in TLD2] + [re.escape(t) for t in sorted(TLD1, key=len, reverse=True)])
PAT = re.compile(r'^([a-z0-9][a-z0-9\-]*(?:\.[a-z0-9\-]+)*?\.(?:' + ALT + r'))(?:(?P<junk>[a-z0-9\-\.]+))?$')

def fix(dom):
    d = dom.lower().strip('.')
    m = PAT.match(d)
    if not m: return d, ''
    return m.group(1), (m.group('junk') or '')

if __name__ == '__main__':
    comps = json.load(open('work/companies.json'))
    chg = 0; out = {}
    for c in comps:
        f, junk = fix(c['domain'])
        out[c['domain']] = f
        if f != c['domain']:
            chg += 1
            if chg <= 15: print(c['domain'], '->', f, '| junk:', junk)
    print('changed', chg, 'of', len(comps))
    json.dump(out, open('work/dommap.json','w'))
