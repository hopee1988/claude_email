import json, collections, re
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

rows = json.load(open('work/final.json'))
wb = Workbook(); wb.remove(wb.active)

H1 = Font(bold=True, size=16, color='1F3864')
HDR = Font(bold=True, color='FFFFFF', size=10)
HDRF = PatternFill('solid', fgColor='1F3864')
B = Font(bold=True)
thin = Side(style='thin', color='D0D7E5')
BRD = Border(left=thin, right=thin, top=thin, bottom=thin)
GREEN = PatternFill('solid', fgColor='E2EFDA'); YELL = PatternFill('solid', fgColor='FFF2CC')
RED = PatternFill('solid', fgColor='FFC7CE'); REDROW = PatternFill('solid', fgColor='FDE9EA')
GREY = PatternFill('solid', fgColor='F2F2F2')
REDTXT = Font(color='9C0006', bold=True, size=10)
REDTXT_N = Font(color='9C0006', size=10)
GRNTXT = Font(color='375623', bold=True, size=10)
YELTXT = Font(color='7F6000', bold=True, size=10)

def vstate(r):
    """yesil / sari / gri / kirmizi"""
    if r['_ver']: return 'ok'
    if r['_partial']: return 'part'
    if r['_live'] and r['_kind'] != 'free': return 'unk'
    return 'bad'

# ---------------- Sheet: Özet ----------------
ws = wb.create_sheet('Özet')
tot = len(rows)
live = sum(1 for r in rows if r['_live']); parked = sum(1 for r in rows if r['_parked'])
nosite = tot - live - parked
free = sum(1 for r in rows if r['_kind'] == 'free')
ver = sum(1 for r in rows if r['_ver']); part = sum(1 for r in rows if r['_partial'])
unclear = sum(1 for r in rows if r['_live'] and not r['_ver'] and not r['_partial'])
failed = tot - ver - part - unclear
emails_all = sorted({e for r in rows for e in r['_emails']})
ver_emails = sorted({e for r in rows for e in r['_emails'] if e in r['_found']})
extra = sorted({f for r in rows for f in r['_found'] if f.split('@')[-1] == r['Alan adı'] and f not in r['_emails']})

ws['A1'] = 'E-posta & Numara Listesi – Doğrulama ve Analiz Özeti'; ws['A1'].font = H1
ws['A2'] = 'Kaynak: e_mail_ve_numaralar.docx  |  Doğrulama tarihi: 5 Kasım 2026  |  Tüm web siteleri canlı olarak sorgulandı'
ws['A2'].font = Font(italic=True, size=9, color='666666')

def block(r0, title, pairs):
    ws.cell(r0, 1, title).font = Font(bold=True, size=12, color='1F3864')
    i = r0 + 1
    for k, v in pairs:
        ws.cell(i, 1, k).font = Font(size=10)
        c = ws.cell(i, 2, v); c.font = B; c.alignment = Alignment(horizontal='left')
        i += 1
    return i + 1

r = 4
r = block(r, 'KAYIT SAYILARI', [
    ('Dokümandan çıkarılan benzersiz firma / kayıt', tot),
    ('Benzersiz e-posta adresi', len(emails_all)),
    ('Benzersiz alan adı (kurumsal)', len({r2['Alan adı'] for r2 in rows if r2['_kind'] == 'dom'})),
    ('Ücretsiz e-posta (gmail/hotmail vb.) kaydı', free),
])
r = block(r, 'WEB SİTESİ DURUMU  (soru: kaç tanesinin web sitesi var?)', [
    ('WEB SİTESİ VAR – canlı ve çalışıyor', live),
    ('Alan adı park/satılık – gerçek site yok', parked),
    ('WEB SİTESİ YOK – alan adı yanıt vermiyor', nosite),
    ('Web sitesi olan kayıtların oranı', '%d%%' % round(100 * live / tot)),
])
r = block(r, 'E-POSTA DOĞRULAMA (sitelerden)', [
    ('DOĞRULANDI – adres firmanın sitesinde birebir bulundu', ver),
    ('KISMİ – site aktif, aynı alan adında e-posta var, bu adres yok', part),
    ('BELİRSİZ – site aktif ama taranan sayfalarda e-posta yok', unclear),
    ('DOĞRULANAMADI – site/alan adı yanıt vermiyor', failed),
    ('Sitede birebir doğrulanan e-posta adresi sayısı', len(ver_emails)),
    ('Sitelerde bulunan EK (listede olmayan) kurumsal e-posta', len(extra)),
])
roles = collections.Counter(r2['Owner / Broker'] for r2 in rows)
r = block(r, 'OWNER / BROKER DAĞILIMI', [(k, v) for k, v in roles.most_common()])
r = block(r, 'YÖNTEM / NOTLAR', [
    ('1', 'Her alan adı için https/http ana sayfa + iletişim/about sayfaları canlı çekildi.'),
    ('2', 'E-posta, firmanın kendi sitesinde metin/mailto olarak aranıp birebir eşleşme ile doğrulandı.'),
    ('3', '"Alan adı yanıt vermiyor" = DNS/sunucu yanıtı yok; bu adreslere gönderilen mailler çoğunlukla geri döner.'),
    ('4', 'Owner / Broker sınıflandırması dokümandaki açıklamalar + firma adı + site başlığından çıkarıldı; kritik kayıtlar için teyit önerilir.'),
    ('5', 'Dokümanda bazı kayıtlar bitişik yazıldığı için alan adları (ör. "...comnordic") otomatik düzeltildi.'),
])
r = block(r, 'RENK KODLARI (Firmalar / Owner & Broker / E-posta detay sayfaları)', [
    ('KIRMIZI satır', 'DOĞRULANAMADI – site/alan adı yanıt vermiyor veya ücretsiz e-posta; adres teyit edilemedi'),
    ('Sarı hücre', 'KISMİ – site aktif, aynı alan adında e-posta var ama bu adres sitede görünmüyor'),
    ('Gri hücre', 'BELİRSİZ – site aktif ama taranan sayfalarda hiç e-posta yok'),
    ('Yeşil hücre', 'DOĞRULANDI – e-posta firmanın kendi sitesinde birebir bulundu'),
])
_leg = {'KIRMIZI satır': (REDROW, REDTXT), 'Sarı hücre': (YELL, YELTXT), 'Gri hücre': (GREY, Font(size=10)), 'Yeşil hücre': (GREEN, GRNTXT)}
for _row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=2):
    if _row[0].value in _leg:
        f, ft = _leg[_row[0].value]
        for _c in _row:
            _c.fill = f
        _row[0].font = ft
ws.column_dimensions['A'].width = 68; ws.column_dimensions['B'].width = 95

# ---------------- Sheet: Firmalar ----------------
COLS = ['Firma', 'Ülke', 'Owner / Broker', 'Ne iş yapıyor (kısa)', 'Web sitesi var mı', 'Web sitesi',
        'Web sitesi durumu', 'Dokümandaki e-posta(lar)', 'E-posta doğrulama', 'Sitede birebir bulunan',
        'Sitede bulunan diğer e-postalar', 'Telefon', 'Site başlığı', 'Alan adı']
ws2 = wb.create_sheet('Firmalar')
ws2.append(COLS)
for c in ws2[1]:
    c.font = HDR; c.fill = HDRF; c.alignment = Alignment(vertical='center', wrap_text=True)
for r2 in rows:
    ws2.append([r2.get(k, '') for k in COLS])
ws2.freeze_panes = 'A2'
ws2.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(COLS)), ws2.max_row)
W = {'Firma': 38, 'Ülke': 13, 'Owner / Broker': 20, 'Ne iş yapıyor (kısa)': 52, 'Web sitesi var mı': 9,
     'Web sitesi': 34, 'Web sitesi durumu': 30, 'Dokümandaki e-posta(lar)': 42, 'E-posta doğrulama': 44,
     'Sitede birebir bulunan': 32, 'Sitede bulunan diğer e-postalar': 40, 'Telefon': 20, 'Site başlığı': 32,
     'Alan adı': 26}
for i, k in enumerate(COLS, 1):
    ws2.column_dimensions[get_column_letter(i)].width = W[k]
iw, iv, ifi = COLS.index('Web sitesi var mı') + 1, COLS.index('E-posta doğrulama') + 1, COLS.index('Web sitesi') + 1
for row, r2 in zip(ws2.iter_rows(min_row=2), rows):
    st = vstate(r2)
    if st == 'bad':                      # DOĞRULANAMAYANLAR: tüm satır kırmızı
        for c in row:
            c.fill = REDROW; c.font = REDTXT_N
        row[iv - 1].fill = RED; row[iv - 1].font = REDTXT
    else:
        row[iv - 1].fill = {'ok': GREEN, 'part': YELL, 'unk': GREY}[st]
        row[iv - 1].font = {'ok': GRNTXT, 'part': YELLTXT_, 'unk': Font(size=10)}[st] if False else {'ok': GRNTXT, 'part': YELTXT, 'unk': Font(size=10)}[st]
    wv = row[iw - 1].value
    row[iw - 1].fill = GREEN if wv == 'VAR' else (YELL if wv == 'PARK' else RED)
    row[iw - 1].font = GRNTXT if wv == 'VAR' else (YELTXT if wv == 'PARK' else REDTXT)
    row[iw - 1].alignment = Alignment(horizontal='center')
    u = row[ifi - 1].value
    if u and st != 'bad':
        row[ifi - 1].hyperlink = u; row[ifi - 1].font = Font(color='0563C1', underline='single', size=10)
ws2.row_dimensions[1].height = 30

# ---------------- Sheet: Owner & Broker ----------------
ws3 = wb.create_sheet('Owner & Broker')
sel = [r2 for r2 in rows if r2['Owner / Broker'] in ('Broker', 'Owner (armatör)', 'Owner + Broker', 'Operatör / ship manager')]
sel.sort(key=lambda x: (x['Owner / Broker'], x['Ülke'] or 'ZZZ', x['Firma'].lower()))
ws3['A1'] = 'Sadece Owner / Broker / Operatör kayıtları (%d firma)' % len(sel); ws3['A1'].font = H1
C3 = ['Owner / Broker', 'Firma', 'Ülke', 'Ne iş yapıyor (kısa)', 'Web sitesi var mı', 'Web sitesi',
      'Dokümandaki e-posta(lar)', 'E-posta doğrulama', 'Telefon']
ws3.append([]); ws3.append(C3)
for c in ws3[3]: c.font = HDR; c.fill = HDRF
for r2 in sel: ws3.append([r2.get(k, '') for k in C3])
ws3.freeze_panes = 'A4'
ws3.auto_filter.ref = 'A3:%s%d' % (get_column_letter(len(C3)), ws3.max_row)
for i, k in enumerate(C3, 1):
    ws3.column_dimensions[get_column_letter(i)].width = {'Owner / Broker': 20, 'Firma': 38, 'Ülke': 13,
        'Ne iş yapıyor (kısa)': 50, 'Web sitesi var mı': 9, 'Web sitesi': 34,
        'Dokümandaki e-posta(lar)': 42, 'E-posta doğrulama': 44, 'Telefon': 20}[k]
for row, r2 in zip(ws3.iter_rows(min_row=4), sel):
    st = vstate(r2)
    if st == 'bad':
        for c in row:
            c.fill = REDROW; c.font = REDTXT_N
        row[7].fill = RED; row[7].font = REDTXT
    else:
        row[7].fill = {'ok': GREEN, 'part': YELL, 'unk': GREY}[st]
    wv = row[4].value
    row[4].fill = GREEN if wv == 'VAR' else (YELL if wv == 'PARK' else RED)
    row[4].font = GRNTXT if wv == 'VAR' else (YELTXT if wv == 'PARK' else REDTXT)
    row[4].alignment = Alignment(horizontal='center')

# ---------------- Sheet: E-posta detay ----------------
ws4 = wb.create_sheet('E-posta detay')
C4 = ['E-posta', 'Firma', 'Ülke', 'Owner / Broker', 'Web sitesi', 'Site aktif mi', 'Sitede bulundu mu', 'Durum']
ws4.append(C4)
for c in ws4[1]: c.font = HDR; c.fill = HDRF
cnt_e = 0
estates = []
for r2 in rows:
    for e in r2['_emails']:
        found = e in r2['_found']
        ws4.append([e, r2['Firma'], r2['Ülke'], r2['Owner / Broker'], r2['Web sitesi'],
                    'EVET' if r2['_live'] else 'HAYIR', 'EVET' if found else 'HAYIR', r2['E-posta doğrulama']])
        estates.append('ok' if found else vstate(r2))
        cnt_e += 1
ws4.freeze_panes = 'A2'
ws4.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(C4)), ws4.max_row)
for i, w in enumerate([40, 36, 13, 20, 32, 11, 16, 44], 1):
    ws4.column_dimensions[get_column_letter(i)].width = w
for row, st in zip(ws4.iter_rows(min_row=2), estates):
    if st == 'bad':
        for c in row:
            c.fill = REDROW; c.font = REDTXT_N
        row[7].fill = RED; row[7].font = REDTXT
    elif st == 'part':
        row[7].fill = YELL
    elif st == 'unk':
        row[7].fill = GREY
    else:
        row[7].fill = GREEN
    for i in (5, 6):
        row[i].fill = GREEN if row[i].value == 'EVET' else RED
        row[i].font = GRNTXT if row[i].value == 'EVET' else REDTXT
        row[i].alignment = Alignment(horizontal='center')

# ---------------- Sheet: Ülke özeti ----------------
ws5 = wb.create_sheet('Ülke özeti')
ws5.append(['Ülke', 'Firma sayısı', 'Web sitesi VAR', 'Site yok/park', 'E-postası doğrulandı', 'Broker', 'Owner', 'Operatör/Manager', 'Acente', 'Diğer'])
for c in ws5[1]: c.font = HDR; c.fill = HDRF
agg = collections.defaultdict(lambda: collections.Counter())
for r2 in rows:
    k = r2['Ülke'] or '(belirsiz)'
    a = agg[k]; a['n'] += 1
    a['live'] += 1 if r2['_live'] else 0
    a['no'] += 0 if r2['_live'] else 1
    a['ver'] += 1 if r2['_ver'] else 0
    ro = r2['Owner / Broker']
    if ro == 'Broker': a['b'] += 1
    elif ro.startswith('Owner'): a['o'] += 1
    elif 'manager' in ro: a['m'] += 1
    elif 'Acente' in ro: a['ag'] += 1
    else: a['d'] += 1
for k, a in sorted(agg.items(), key=lambda x: -x[1]['n']):
    ws5.append([k, a['n'], a['live'], a['no'], a['ver'], a['b'], a['o'], a['m'], a['ag'], a['d']])
ws5.freeze_panes = 'A2'
for i, w in enumerate([22, 13, 14, 14, 20, 10, 10, 18, 10, 10], 1):
    ws5.column_dimensions[get_column_letter(i)].width = w

# ---------------- Sheet: Sitelerden ek e-postalar ----------------
ws6 = wb.create_sheet('Sitelerden ek e-postalar')
ws6.append(['Firma', 'Alan adı', 'Ülke', 'Sitede bulunan ek e-posta', 'Web sitesi'])
for c in ws6[1]: c.font = HDR; c.fill = HDRF
n6 = 0
for r2 in rows:
    for f in r2['_found']:
        if f.split('@')[-1] == r2['Alan adı'] and f not in r2['_emails']:
            ws6.append([r2['Firma'], r2['Alan adı'], r2['Ülke'], f, r2['Web sitesi']]); n6 += 1
ws6.freeze_panes = 'A2'
ws6.auto_filter.ref = 'A1:E%d' % ws6.max_row
for i, w in enumerate([38, 26, 13, 42, 34], 1):
    ws6.column_dimensions[get_column_letter(i)].width = w

out = '/home/user/claude_email/denizcilik_firmalari_dogrulama.xlsx'
wb.save(out)
print('saved', out, '| firmalar', len(rows), '| e-posta satiri', cnt_e, '| ek e-posta', n6)
