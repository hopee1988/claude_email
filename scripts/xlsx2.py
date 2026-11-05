import json, collections
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

rows = json.load(open('work/filtered.json'))
wb = Workbook(); wb.remove(wb.active)
HDR = Font(bold=True, color='FFFFFF', size=10); HDRF = PatternFill('solid', fgColor='1F3864')
H1 = Font(bold=True, size=15, color='1F3864')
GREEN = PatternFill('solid', fgColor='E2EFDA'); YELL = PatternFill('solid', fgColor='FFF2CC')
GREY = PatternFill('solid', fgColor='F2F2F2'); RED = PatternFill('solid', fgColor='FFC7CE')
REDROW = PatternFill('solid', fgColor='FDE9EA')
REDTXT = Font(color='9C0006', bold=True, size=10); REDTXT_N = Font(color='9C0006', size=10)
GRNTXT = Font(color='375623', bold=True, size=10); YELTXT = Font(color='7F6000', bold=True, size=10)
ROLEF = {'Owner (armatör)': PatternFill('solid', fgColor='DDEBF7'), 'Owner + Broker': PatternFill('solid', fgColor='DDEBF7'),
         'Broker': PatternFill('solid', fgColor='E4DFEC'), 'Chartering / broker': PatternFill('solid', fgColor='E4DFEC'),
         'Operatör / ship manager': PatternFill('solid', fgColor='FDE9D9'), 'Operatör / operations': PatternFill('solid', fgColor='FDE9D9')}

COLS = ['Firma', 'Ülke', 'Rol (Owner/Chartering/Operation)', 'Sektör / ne iş yapıyor', 'E-posta',
        'Departman (mail eki)', 'Telefon(lar)', 'Web sitesi', 'Web sitesi durumu', 'E-posta doğrulama',
        'Sitede bulunan diğer e-postalar', 'Site başlığı', 'Alan adı', 'Kaynak metin (dokümandan)']
W = [36, 13, 24, 44, 36, 18, 26, 32, 30, 42, 38, 28, 24, 60]

def sheet(name, data, title=None):
    ws = wb.create_sheet(name)
    start = 1
    if title:
        ws['A1'] = title; ws['A1'].font = H1; ws.append([]); start = 3
    ws.append(COLS)
    for c in ws[start + 0 if not title else 3]:
        c.font = HDR; c.fill = HDRF; c.alignment = Alignment(vertical='center', wrap_text=True)
    hdr_row = ws.max_row
    for r in data:
        ws.append([r.get(k, '') for k in COLS])
    ws.freeze_panes = 'A%d' % (hdr_row + 1)
    ws.auto_filter.ref = 'A%d:%s%d' % (hdr_row, get_column_letter(len(COLS)), ws.max_row)
    for i, w in enumerate(W, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[hdr_row].height = 30
    iv, iw, iu, ir = COLS.index('E-posta doğrulama'), COLS.index('Web sitesi durumu'), COLS.index('Web sitesi'), COLS.index('Rol (Owner/Chartering/Operation)')
    for row, r in zip(ws.iter_rows(min_row=hdr_row + 1), data):
        st = r['_st']
        if st == 'bad':
            for c in row: c.fill = REDROW; c.font = REDTXT_N
            row[iv].fill = RED; row[iv].font = REDTXT
            row[iw].fill = RED; row[iw].font = REDTXT
        else:
            row[iv].fill = {'ok': GREEN, 'part': YELL, 'unk': GREY}[st]
            row[iv].font = {'ok': GRNTXT, 'part': YELTXT, 'unk': Font(size=10)}[st]
            if r['_live']:
                row[iw].fill = GREEN; row[iw].font = GRNTXT
            u = row[iu].value
            if u:
                row[iu].hyperlink = u; row[iu].font = Font(color='0563C1', underline='single', size=10)
            row[ir].fill = ROLEF.get(r['_role'], GREY)
    return ws

sheet('TÜM LİSTE', rows)
sheet('Owner (armatör)', [r for r in rows if r['_role'].startswith('Owner')], 'Owner / armatör kayıtları')
sheet('Chartering & Broker', [r for r in rows if 'Broker' in r['_role'] or 'Chartering' in r['_role']], 'Chartering / broker kayıtları')
sheet('Operation', [r for r in rows if r['_role'].startswith('Operatör')], 'Operation / ship management kayıtları')
sheet('Sadece doğrulanmış', [r for r in rows if r['_st'] in ('ok', 'part')], 'E-postası siteden doğrulanan kayıtlar (yeşil + sarı)')

# --- Özet ---
ws = wb.create_sheet('Özet', 0)
ws['A1'] = 'Owner / Chartering / Operation listesi – yat sektörü çıkarılmış'; ws['A1'].font = H1
ws['A2'] = 'Kaynak: e_mail_ve_numaralar.docx | Web siteleri ve e-postalar canlı doğrulandı'
ws['A2'].font = Font(italic=True, size=9, color='666666')
r = 4
def block(r0, t, pairs):
    ws.cell(r0, 1, t).font = Font(bold=True, size=12, color='1F3864')
    i = r0 + 1
    for k, v in pairs:
        ws.cell(i, 1, k); ws.cell(i, 2, v).font = Font(bold=True); i += 1
    return i + 1
st = collections.Counter(x['_st'] for x in rows)
r = block(r, 'KAPSAM', [
    ('Dokümandaki toplam e-posta kaydı', 2642),
    ('Silinen – yat / marina / tekne / turizm ile ilgili', 1207),
    ('Silinen – owner/chartering/operation dışı (acente, tedarik, servis vb.)', 928),
    ('KALAN e-posta kaydı', len(rows)),
    ('Kalan firma (alan adı) sayısı', len({x['Alan adı'] for x in rows})),
])
r = block(r, 'ROL DAĞILIMI', [(k, v) for k, v in collections.Counter(x['_role'] for x in rows).most_common()])
r = block(r, 'E-POSTA DOĞRULAMA', [
    ('DOĞRULANDI – adres firmanın sitesinde birebir bulundu', st['ok']),
    ('KISMİ – site aktif, aynı alan adında e-posta var', st['part']),
    ('BELİRSİZ – site aktif ama sayfalarda e-posta yok', st['unk']),
    ('DOĞRULANAMADI (KIRMIZI) – site/alan adı yanıt vermiyor veya ücretsiz e-posta', st['bad']),
    ('Web sitesi aktif olan kayıt', sum(1 for x in rows if x['_live'])),
])
r = block(r, 'RENK KODLARI', [
    ('KIRMIZI satır', 'DOĞRULANAMADI – site/alan adı ölü; bu adrese atılan mail büyük olasılıkla geri döner'),
    ('Sarı hücre', 'KISMİ – site aktif, aynı alan adında başka e-posta var'),
    ('Gri hücre', 'BELİRSİZ – site aktif ama e-posta bulunamadı'),
    ('Yeşil hücre', 'DOĞRULANDI – e-posta sitede birebir bulundu'),
    ('Mavi (rol)', 'Owner / armatör'), ('Mor (rol)', 'Chartering / broker'), ('Turuncu (rol)', 'Operation / ship manager'),
])
leg = {'KIRMIZI satır': (REDROW, REDTXT), 'Sarı hücre': (YELL, YELTXT), 'Gri hücre': (GREY, Font(size=10)),
       'Yeşil hücre': (GREEN, GRNTXT), 'Mavi (rol)': (ROLEF['Owner (armatör)'], Font(size=10)),
       'Mor (rol)': (ROLEF['Broker'], Font(size=10)), 'Turuncu (rol)': (ROLEF['Operatör / operations'], Font(size=10))}
for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=2):
    if row[0].value in leg:
        f, ft = leg[row[0].value]
        for c in row: c.fill = f
        row[0].font = ft
ws.column_dimensions['A'].width = 72; ws.column_dimensions['B'].width = 90

out = '/home/user/claude_email/owner_chartering_operation_listesi.xlsx'
wb.save(out)
print('saved', out, '| kayıt', len(rows))
