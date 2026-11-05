import json, collections
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

import re, sys
sys.path.insert(0, 'work')
from classify import fallback_name
rows = json.load(open('work/chartops.json'))

def _norm(x): return re.sub(r'[^a-z0-9]', '', (x or '').lower())
def _base(dom):
    p = dom.split('.')
    b = p[-3] if (len(p) >= 3 and len(p[-2]) <= 3) else (p[-2] if len(p) >= 2 else p[0])
    return re.sub(r'[^a-z0-9]', '', b.lower())

_b1 = {o['domain']: o for o in json.load(open('work/bimco.json'))}
for _o in json.load(open('work/bimco2.json')):
    if _o.get('bimco') or _o['domain'] not in _b1: _b1[_o['domain']] = _o

_EV = {
 'jadroplov.hr': "Ana sayfada BIMCO logosu (img alt/title: 'Bimco')",
 'hollandhellenic.gr': 'Ana sayfada BIMCO logosu (bimco.webp görseli)',
 'altamarpanama.com': "Sertifikalar bölümünde BIMCO member logosu – 'Member since 2021'",
 'emco-shipping.com': "Ana sayfada bimco.org'a link + BIMCO logosu ve 'Bimco' başlığı",
}

def _bimco(dom, live):
    o = _b1.get(dom)
    if o and o.get('bimco'):
        return ('SİTESİNDE BIMCO GEÇİYOR – muhtemel üye', _EV.get(dom, o.get('evidence', ''))[:300], o.get('page', ''))
    if not live:
        return ('Kontrol edilemedi – site/alan adı ölü', '', '')
    return ('Sitesinde BIMCO referansı yok', '', '')

for _r in rows:                      # firma adı alan adıyla uyuşmuyorsa alan adından türet
    _b = _base(_r['Alan adı'])
    _r['Dokümandaki ad/açıklama'] = _r['Firma']
    _st2, _ev, _pg = _bimco(_r['Alan adı'], _r['_live'])
    _r['BIMCO durumu'] = _st2; _r['BIMCO kanıtı (site metni)'] = _ev; _r['BIMCO kanıt sayfası'] = _pg
    _r['_bim'] = _st2.startswith('SİTESİNDE')
    if _b and _b not in _norm(_r['Firma']) and not (len(_b) > 5 and _b[:6] in _norm(_r['Firma'])):
        _r['Firma'] = fallback_name(_r['Alan adı'])
RANK = {'ok': 3, 'part': 2, 'unk': 1, 'bad': 0}
VERTXT = {'ok': 'DOĞRULANDI – adres sitede birebir bulundu',
          'part': 'KISMİ – site aktif, aynı alan adında e-posta var',
          'unk': 'BELİRSİZ – site aktif, sayfalarda e-posta yok',
          'bad': 'DOĞRULANAMADI – site/alan adı yanıt vermiyor'}

# ---- company level ----
g = collections.OrderedDict()
for r in sorted(rows, key=lambda x: (x['Ülke'] or 'ZZZ', x['Firma'].lower())):
    k = r['Alan adı']
    c = g.setdefault(k, {'Firma': r['Firma'], 'Ülke': r['Ülke'], 'Sektör / ne iş yapıyor': r['Sektör / ne iş yapıyor'],
                         'Rol (sektördeki konumu)': r['Rol (sektördeki konumu)'], 'ch': [], 'op': [], 'ph': [],
                         'Web sitesi': r['Web sitesi'], 'Web sitesi durumu': r['Web sitesi durumu'],
                         'Sitede bulunan diğer e-postalar': r['Sitede bulunan diğer e-postalar'],
                         'Site başlığı': r['Site başlığı'], 'Alan adı': k,
                         'Kaynak metin (dokümandan)': r['Kaynak metin (dokümandan)'], 'st': 'bad', '_live': r['_live'],
                         'doc': r['Dokümandaki ad/açıklama'], 'bim': r['BIMCO durumu'],
                         'bev': r['BIMCO kanıtı (site metni)'], 'bpg': r['BIMCO kanıt sayfası'], '_bim': r['_bim']})
    (c['ch'] if r['_mt'].startswith('Chartering') else c['op']).append(r['E-posta'])
    for p in r['_phones']:
        if p not in c['ph']: c['ph'].append(p)
    if RANK[r['_st']] > RANK[c['st']]: c['st'] = r['_st']
    if len(r['Firma']) > len(c['Firma']): c['Firma'] = r['Firma']

comps = []
for c in g.values():
    c['ch'] = list(dict.fromkeys(c['ch'])); c['op'] = list(dict.fromkeys(c['op']))
    comps.append({'Firma': c['Firma'], 'Ülke': c['Ülke'],
                  'Mail tipi': 'Chartering + Operation' if (c['ch'] and c['op']) else ('Chartering' if c['ch'] else 'Operation'),
                  'Chartering e-posta': ', '.join(c['ch']), 'Operation e-posta': ', '.join(c['op']),
                  'Telefon(lar)': ' / '.join(c['ph']), 'Rol (sektördeki konumu)': c['Rol (sektördeki konumu)'],
                  'Sektör / ne iş yapıyor': c['Sektör / ne iş yapıyor'], 'Web sitesi': c['Web sitesi'],
                  'Web sitesi durumu': c['Web sitesi durumu'], 'E-posta doğrulama': VERTXT[c['st']],
                  'Sitede bulunan diğer e-postalar': c['Sitede bulunan diğer e-postalar'],
                  'Site başlığı': c['Site başlığı'], 'Alan adı': c['Alan adı'],
                  'BIMCO durumu': c['bim'], 'BIMCO kanıtı (site metni)': c['bev'], 'BIMCO kanıt sayfası': c['bpg'],
                  '_bim': c['_bim'], 'Dokümandaki ad/açıklama': c['doc'], 'Kaynak metin (dokümandan)': c['Kaynak metin (dokümandan)'],
                  '_st': c['st'], '_live': c['_live'],
                  '_mt': 'Chartering + Operation' if (c['ch'] and c['op']) else ('Chartering' if c['ch'] else 'Operation')})

wb = Workbook(); wb.remove(wb.active)
HDR = Font(bold=True, color='FFFFFF', size=10); HDRF = PatternFill('solid', fgColor='1F3864')
H1 = Font(bold=True, size=15, color='1F3864')
GREEN = PatternFill('solid', fgColor='E2EFDA'); YELL = PatternFill('solid', fgColor='FFF2CC')
GREY = PatternFill('solid', fgColor='F2F2F2'); RED = PatternFill('solid', fgColor='FFC7CE')
REDROW = PatternFill('solid', fgColor='FDE9EA')
REDTXT = Font(color='9C0006', bold=True, size=10); REDTXT_N = Font(color='9C0006', size=10)
GRNTXT = Font(color='375623', bold=True, size=10); YELTXT = Font(color='7F6000', bold=True, size=10)
MTF = {'Chartering': PatternFill('solid', fgColor='E4DFEC'), 'Operation': PatternFill('solid', fgColor='FDE9D9'),
       'Chartering + Operation': PatternFill('solid', fgColor='DDEBF7')}

C1 = ['Firma', 'Ülke', 'Mail tipi', 'Chartering e-posta', 'Operation e-posta', 'Telefon(lar)',
      'Rol (sektördeki konumu)', 'Sektör / ne iş yapıyor', 'Web sitesi', 'Web sitesi durumu',
      'E-posta doğrulama', 'BIMCO durumu', 'BIMCO kanıtı (site metni)', 'BIMCO kanıt sayfası',
      'Sitede bulunan diğer e-postalar', 'Site başlığı', 'Alan adı',
      'Dokümandaki ad/açıklama', 'Kaynak metin (dokümandan)']
W1 = [34, 13, 20, 38, 38, 28, 22, 42, 32, 30, 42, 34, 50, 34, 38, 26, 24, 40, 60]
C2 = ['Firma', 'Ülke', 'Mail tipi', 'E-posta', 'Departman (mail eki)', 'Telefon(lar)', 'Rol (sektördeki konumu)',
      'Sektör / ne iş yapıyor', 'Web sitesi', 'Web sitesi durumu', 'E-posta doğrulama',
      'BIMCO durumu', 'Sitede bulunan diğer e-postalar', 'Alan adı', 'Dokümandaki ad/açıklama',
      'Kaynak metin (dokümandan)']
W2 = [34, 13, 20, 38, 20, 26, 22, 42, 32, 30, 42, 34, 38, 24, 40, 60]

def sheet(name, data, cols, widths, title=None):
    ws = wb.create_sheet(name)
    if title:
        ws['A1'] = title; ws['A1'].font = H1; ws.append([])
    ws.append(cols)
    hdr = ws.max_row
    for c in ws[hdr]:
        c.font = HDR; c.fill = HDRF; c.alignment = Alignment(vertical='center', wrap_text=True)
    for r in data: ws.append([r.get(k, '') for k in cols])
    ws.freeze_panes = 'A%d' % (hdr + 1)
    ws.auto_filter.ref = 'A%d:%s%d' % (hdr, get_column_letter(len(cols)), ws.max_row)
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[hdr].height = 30
    iv, iw, iu, im = cols.index('E-posta doğrulama'), cols.index('Web sitesi durumu'), cols.index('Web sitesi'), cols.index('Mail tipi')
    for row, r in zip(ws.iter_rows(min_row=hdr + 1), data):
        if r['_st'] == 'bad':
            for c in row: c.fill = REDROW; c.font = REDTXT_N
            row[iv].fill = RED; row[iv].font = REDTXT
            row[iw].fill = RED; row[iw].font = REDTXT
        else:
            row[iv].fill = {'ok': GREEN, 'part': YELL, 'unk': GREY}[r['_st']]
            row[iv].font = {'ok': GRNTXT, 'part': YELTXT, 'unk': Font(size=10)}[r['_st']]
            if r['_live']: row[iw].fill = GREEN; row[iw].font = GRNTXT
            u = row[iu].value
            if u: row[iu].hyperlink = u; row[iu].font = Font(color='0563C1', underline='single', size=10)
        row[im].fill = MTF[r['_mt']]; row[im].alignment = Alignment(horizontal='center')
        if 'BIMCO durumu' in cols:
            ib = cols.index('BIMCO durumu')
            if r.get('_bim'):
                row[ib].fill = GREEN; row[ib].font = GRNTXT
            elif r['_st'] != 'bad':
                row[ib].fill = GREY
    return ws

sheet('FİRMALAR', comps, C1, W1)
sheet('Chartering', [c for c in comps if c['_mt'] != 'Operation'], C1, W1, 'Chartering maili olan firmalar')
sheet('Operation', [c for c in comps if c['_mt'] != 'Chartering'], C1, W1, 'Operation maili olan firmalar')
sheet('Doğrulanmış firmalar', [c for c in comps if c['_st'] in ('ok', 'part')], C1, W1,
      'E-postası siteden doğrulanan firmalar (yeşil + sarı)')
sheet('E-posta detay', rows, C2, W2)

ws = wb.create_sheet('Özet', 0)
ws['A1'] = 'Chartering & Operation maili olan firmalar'; ws['A1'].font = H1
ws['A2'] = 'Kaynak: e_mail_ve_numaralar.docx | Yat sektörü çıkarıldı | Web siteleri ve e-postalar canlı doğrulandı'
ws['A2'].font = Font(italic=True, size=9, color='666666')
def block(r0, t, pairs):
    ws.cell(r0, 1, t).font = Font(bold=True, size=12, color='1F3864')
    i = r0 + 1
    for k, v in pairs:
        ws.cell(i, 1, k); ws.cell(i, 2, v).font = Font(bold=True); i += 1
    return i + 1
st = collections.Counter(c['_st'] for c in comps)
r = block(4, 'KAPSAM', [
    ('Dokümandaki toplam e-posta kaydı', 2642),
    ('Silinen – yat / marina / tekne / turizm', 1015),
    ('Silinen – chartering/operation adresi olmayan', 1521),
    ('KALAN e-posta adresi', len(rows)),
    ('KALAN FİRMA sayısı', len(comps)),
])
r = block(r, 'MAİL TİPİ (firma bazında)', [(k, v) for k, v in collections.Counter(c['_mt'] for c in comps).most_common()])
r = block(r, 'DOĞRULAMA (firma bazında)', [
    ('DOĞRULANDI – adres sitede birebir bulundu', st['ok']),
    ('KISMİ – site aktif, aynı alan adında e-posta var', st['part']),
    ('BELİRSİZ – site aktif ama sayfalarda e-posta yok', st['unk']),
    ('DOĞRULANAMADI (KIRMIZI) – site/alan adı yanıt vermiyor', st['bad']),
    ('Web sitesi aktif olan firma', sum(1 for c in comps if c['_live'])),
])
r = block(r, 'BIMCO ÜYELİK KONTROLÜ', [
    ('Sitesinde BIMCO referansı bulunan firma', sum(1 for c in comps if c.get('_bim'))),
    ('Sitesinde BIMCO referansı olmayan (site aktif)', sum(1 for c in comps if not c.get('_bim') and c['_live'])),
    ('Kontrol edilemedi – site/alan adı ölü', sum(1 for c in comps if not c.get('_bim') and not c['_live'])),
    ('NOT', 'BIMCO üye dizini herkese açık değil (üye girişi gerekiyor); bu kolon firmanın KENDİ sitesindeki BIMCO beyanına dayanır.'),
    ('NOT', 'Referans bulunmaması üye olmadığı anlamına gelmez – çoğu firma üyeliğini sitesinde yazmaz.'),
    ('KESİN DOĞRULAMA', 'bimco.org üye girişi ile Member Search; erişiminiz varsa liste bu kolona işlenebilir.'),
])
r = block(r, 'RENK KODLARI', [
    ('KIRMIZI satır', 'DOĞRULANAMADI – site/alan adı ölü; mail büyük olasılıkla geri döner'),
    ('Sarı hücre', 'KISMİ – site aktif, aynı alan adında başka e-posta var'),
    ('Gri hücre', 'BELİRSİZ – site aktif ama e-posta bulunamadı'),
    ('Yeşil hücre', 'DOĞRULANDI – e-posta sitede birebir bulundu'),
    ('Mor (mail tipi)', 'Chartering'), ('Turuncu (mail tipi)', 'Operation'), ('Mavi (mail tipi)', 'Chartering + Operation'),
])
leg = {'KIRMIZI satır': (REDROW, REDTXT), 'Sarı hücre': (YELL, YELTXT), 'Gri hücre': (GREY, Font(size=10)),
       'Yeşil hücre': (GREEN, GRNTXT), 'Mor (mail tipi)': (MTF['Chartering'], Font(size=10)),
       'Turuncu (mail tipi)': (MTF['Operation'], Font(size=10)), 'Mavi (mail tipi)': (MTF['Chartering + Operation'], Font(size=10))}
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=2):
    if row[0].value in leg:
        f, ft = leg[row[0].value]
        for c in row: c.fill = f
        row[0].font = ft
ws.column_dimensions['A'].width = 70; ws.column_dimensions['B'].width = 88

out = '/home/user/claude_email/chartering_operation_firmalari.xlsx'
wb.save(out)
print('saved', out, '| firma', len(comps), '| e-posta', len(rows))
print(collections.Counter(c['_mt'] for c in comps).most_common(), dict(st))
