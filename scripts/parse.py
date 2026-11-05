import re, html, json, unicodedata

t = open('doc.txt', encoding='utf8').read()
t = html.unescape(t)

EMOJI_MARK = '\U0001F4E7\U0001F4DE\U0001F4CD\U0001F4F1\U0001F310\U0001F4CC\U0001F539\U0001F527\U0001F4E9☎⚓⛵\U0001F6A2\U0001F6E5\U0001F464\U0001F4A1\U0001F3E2\U0001F6E0✉'

COUNTRIES = {
 'italya':'Italy','italy':'Italy','i̇talya':'Italy','estonia':'Estonia','estonya':'Estonia',
 'denmark':'Denmark','danimarka':'Denmark','finland':'Finland','finlandiya':'Finland',
 'sweden':'Sweden','isveç':'Sweden','i̇sveç':'Sweden','malta':'Malta','gibraltar':'Gibraltar',
 'yeni zelanda':'New Zealand','new zealand':'New Zealand','hindistan':'India','india':'India',
 'hollanda':'Netherlands','netherlands':'Netherlands','singapur':'Singapore','singapore':'Singapore',
 'yunanistan':'Greece','greece':'Greece','portekiz':'Portugal','portugal':'Portugal',
 'türkiye':'Turkey','turkey':'Turkey','bulgaristan':'Bulgaria','bulgaria':'Bulgaria',
 'monaco':'Monaco','karadağ':'Montenegro','montenegro':'Montenegro','fransa':'France','france':'France',
 'ispanya':'Spain','i̇spanya':'Spain','spain':'Spain','uk':'UK','ingiltere':'UK','birleşik krallık':'UK',
 'norveç':'Norway','norway':'Norway','hırvatistan':'Croatia','croatia':'Croatia','kıbrıs':'Cyprus','cyprus':'Cyprus',
 'i̇sviçre':'Switzerland','isviçre':'Switzerland','switzerland':'Switzerland','almanya':'Germany','germany':'Germany',
 'belçika':'Belgium','belgium':'Belgium','polonya':'Poland','poland':'Poland','letonya':'Latvia','latvia':'Latvia',
 'litvanya':'Lithuania','lithuania':'Lithuania','romanya':'Romania','romania':'Romania','ukrayna':'Ukraine','ukraine':'Ukraine',
 'rusya':'Russia','russia':'Russia','abd':'USA','usa':'USA','amerika':'USA','kanada':'Canada','canada':'Canada',
 'avustralya':'Australia','australia':'Australia','japonya':'Japan','japan':'Japan','çin':'China','china':'China',
 'güney kore':'South Korea','korea':'South Korea','bae':'UAE','uae':'UAE','dubai':'UAE','katar':'Qatar','qatar':'Qatar',
 'suudi':'Saudi Arabia','mısır':'Egypt','egypt':'Egypt','i̇srail':'Israel','israel':'Israel','lübnan':'Lebanon',
 'slovenya':'Slovenia','slovenia':'Slovenia','arnavutluk':'Albania','albania':'Albania','i̇rlanda':'Ireland','ireland':'Ireland',
 'i̇zlanda':'Iceland','iceland':'Iceland','brezilya':'Brazil','brazil':'Brazil','panama':'Panama','liberya':'Liberia',
 'endonezya':'Indonesia','indonesia':'Indonesia','malezya':'Malaysia','malaysia':'Malaysia','filipinler':'Philippines',
 'philippines':'Philippines','vietnam':'Vietnam','tayland':'Thailand','thailand':'Thailand','hong kong':'Hong Kong',
 'tunus':'Tunisia','tunisia':'Tunisia','fas':'Morocco','morocco':'Morocco','cezayir':'Algeria','algeria':'Algeria',
 'libya':'Libya','güney afrika':'South Africa','south africa':'South Africa','nijerya':'Nigeria','nigeria':'Nigeria',
 'gana':'Ghana','kenya':'Kenya','umman':'Oman','oman':'Oman','kuveyt':'Kuwait','kuwait':'Kuwait','bahreyn':'Bahrain',
 'i̇ran':'Iran','pakistan':'Pakistan','bangladeş':'Bangladesh','bangladesh':'Bangladesh','sri lanka':'Sri Lanka',
 'macaristan':'Hungary','çekya':'Czechia','avusturya':'Austria','austria':'Austria','lüksemburg':'Luxembourg',
 'faroe':'Faroe Islands','grönland':'Greenland','sırbistan':'Serbia','karayipler':'Caribbean','meksika':'Mexico','mexico':'Mexico',
 'arjantin':'Argentina','şili':'Chile','chile':'Chile','peru':'Peru','kolombiya':'Colombia','uruguay':'Uruguay',
}
FLAG_TO_COUNTRY = {}
import re as _re
def flag_name(s):
    # regional indicator pairs
    try:
        a,b = s[0],s[1]
        return chr(ord(a)-0x1F1E6+ord('A'))+chr(ord(b)-0x1F1E6+ord('A'))
    except Exception:
        return None
ISO2 = {'IT':'Italy','EE':'Estonia','DK':'Denmark','FI':'Finland','SE':'Sweden','MT':'Malta','GI':'Gibraltar',
 'NZ':'New Zealand','IN':'India','NL':'Netherlands','SG':'Singapore','GR':'Greece','PT':'Portugal','TR':'Turkey',
 'BG':'Bulgaria','MC':'Monaco','ME':'Montenegro','FR':'France','ES':'Spain','GB':'UK','NO':'Norway','HR':'Croatia',
 'CY':'Cyprus','CH':'Switzerland','DE':'Germany','BE':'Belgium','PL':'Poland','LV':'Latvia','LT':'Lithuania',
 'RO':'Romania','UA':'Ukraine','RU':'Russia','US':'USA','CA':'Canada','AU':'Australia','JP':'Japan','CN':'China',
 'KR':'South Korea','AE':'UAE','QA':'Qatar','SA':'Saudi Arabia','EG':'Egypt','IL':'Israel','LB':'Lebanon',
 'SI':'Slovenia','AL':'Albania','IE':'Ireland','IS':'Iceland','BR':'Brazil','PA':'Panama','LR':'Liberia',
 'ID':'Indonesia','MY':'Malaysia','PH':'Philippines','VN':'Vietnam','TH':'Thailand','HK':'Hong Kong','TN':'Tunisia',
 'MA':'Morocco','DZ':'Algeria','LY':'Libya','ZA':'South Africa','NG':'Nigeria','GH':'Ghana','KE':'Kenya','OM':'Oman',
 'KW':'Kuwait','BH':'Bahrain','IR':'Iran','PK':'Pakistan','BD':'Bangladesh','LK':'Sri Lanka','HU':'Hungary',
 'CZ':'Czechia','AT':'Austria','LU':'Luxembourg','FO':'Faroe Islands','GL':'Greenland','RS':'Serbia','MX':'Mexico',
 'AR':'Argentina','CL':'Chile','PE':'Peru','CO':'Colombia','UY':'Uruguay','GE':'Georgia','MD':'Moldova','SK':'Slovakia',
 'TW':'Taiwan','VE':'Venezuela','EC':'Ecuador','DO':'Dominican Rep.','JM':'Jamaica','BS':'Bahamas','BM':'Bermuda',
 'KY':'Cayman Islands','VG':'British Virgin Is.','MH':'Marshall Islands','CY2':'Cyprus'}

TLD_COUNTRY = {'it':'Italy','ee':'Estonia','dk':'Denmark','fi':'Finland','se':'Sweden','mt':'Malta','gi':'Gibraltar',
 'nz':'New Zealand','in':'India','nl':'Netherlands','sg':'Singapore','gr':'Greece','pt':'Portugal','tr':'Turkey',
 'bg':'Bulgaria','mc':'Monaco','me':'Montenegro','fr':'France','es':'Spain','uk':'UK','no':'Norway','hr':'Croatia',
 'cy':'Cyprus','ch':'Switzerland','de':'Germany','be':'Belgium','pl':'Poland','lv':'Latvia','lt':'Lithuania',
 'ro':'Romania','ua':'Ukraine','ru':'Russia','us':'USA','ca':'Canada','au':'Australia','jp':'Japan','cn':'China',
 'kr':'South Korea','ae':'UAE','qa':'Qatar','sa':'Saudi Arabia','eg':'Egypt','il':'Israel','lb':'Lebanon',
 'si':'Slovenia','al':'Albania','ie':'Ireland','is':'Iceland','br':'Brazil','pa':'Panama','lr':'Liberia',
 'id':'Indonesia','my':'Malaysia','ph':'Philippines','vn':'Vietnam','th':'Thailand','hk':'Hong Kong','tn':'Tunisia',
 'ma':'Morocco','dz':'Algeria','ly':'Libya','za':'South Africa','ng':'Nigeria','gh':'Ghana','ke':'Kenya','om':'Oman',
 'kw':'Kuwait','bh':'Bahrain','ir':'Iran','pk':'Pakistan','bd':'Bangladesh','lk':'Sri Lanka','hu':'Hungary',
 'cz':'Czechia','at':'Austria','lu':'Luxembourg','fo':'Faroe Islands','gl':'Greenland','rs':'Serbia','mx':'Mexico',
 'ar':'Argentina','cl':'Chile','pe':'Peru','co':'Colombia','uy':'Uruguay','ge':'Georgia','md':'Moldova','sk':'Slovakia',
 'tw':'Taiwan'}

PHONE_CC = [('+971','UAE'),('+974','Qatar'),('+966','Saudi Arabia'),('+968','Oman'),('+965','Kuwait'),('+973','Bahrain'),
 ('+372','Estonia'),('+371','Latvia'),('+370','Lithuania'),('+358','Finland'),('+356','Malta'),('+350','Gibraltar'),
 ('+351','Portugal'),('+352','Luxembourg'),('+353','Ireland'),('+354','Iceland'),('+355','Albania'),('+357','Cyprus'),
 ('+359','Bulgaria'),('+377','Monaco'),('+378','San Marino'),('+380','Ukraine'),('+381','Serbia'),('+382','Montenegro'),
 ('+385','Croatia'),('+386','Slovenia'),('+387','Bosnia'),('+389','N. Macedonia'),('+420','Czechia'),('+421','Slovakia'),
 ('+423','Liechtenstein'),('+298','Faroe Islands'),('+299','Greenland'),('+212','Morocco'),('+213','Algeria'),
 ('+216','Tunisia'),('+218','Libya'),('+220','Gambia'),('+233','Ghana'),('+234','Nigeria'),('+254','Kenya'),
 ('+27','South Africa'),('+30','Greece'),('+31','Netherlands'),('+32','Belgium'),('+33','France'),('+34','Spain'),
 ('+36','Hungary'),('+39','Italy'),('+40','Romania'),('+41','Switzerland'),('+43','Austria'),('+44','UK'),
 ('+45','Denmark'),('+46','Sweden'),('+47','Norway'),('+48','Poland'),('+49','Germany'),('+51','Peru'),('+52','Mexico'),
 ('+54','Argentina'),('+55','Brazil'),('+56','Chile'),('+57','Colombia'),('+58','Venezuela'),('+60','Malaysia'),
 ('+61','Australia'),('+62','Indonesia'),('+63','Philippines'),('+64','New Zealand'),('+65','Singapore'),('+66','Thailand'),
 ('+81','Japan'),('+82','South Korea'),('+84','Vietnam'),('+86','China'),('+852','Hong Kong'),('+886','Taiwan'),
 ('+90','Turkey'),('+91','India'),('+92','Pakistan'),('+94','Sri Lanka'),('+880','Bangladesh'),('+98','Iran'),
 ('+961','Lebanon'),('+962','Jordan'),('+964','Iraq'),('+972','Israel'),('+20','Egypt'),('+1','USA/Canada'),('+7','Russia/KZ')]

# ---- segment the text ----
# Put newline before record starts
txt = t
txt = re.sub(r'(?<!\d)(\d{1,3})\s*[\)\.]\s+', r'\n@@\1) ', txt)   # "1) " numbering
txt = re.sub(r'([\U0001F4CC⛔\U0001F539⚓\U0001F6A2\U0001F6E5\U0001F535\U0001F538])\s*(?=[A-ZÇĞİÖŞÜ])', r'\n@@\1', txt)
lines = [l.strip() for l in txt.split('\n')]

EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
PHONE_RE = re.compile(r'\+\d[\d\s\-\./\(\)]{5,}\d')
URL_RE = re.compile(r'(?:https?://|www\.)[A-Za-z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+', re.I)

records = []
FLAG_RE = re.compile(r'[\U0001F1E6-\U0001F1FF]{2}')
for raw in lines:
    if not raw: continue
    s = raw.lstrip('@@').strip()
    emails = EMAIL_RE.findall(s)
    if not emails:
        continue
    # country candidates found ANYWHERE in this same paste/line (no cross-line carry-over)
    cc_hits = []
    for fm in FLAG_RE.finditer(s[:400]):
        cc = flag_name(fm.group(0))
        if cc in ISO2: cc_hits.append(ISO2[cc])
    head = re.sub(r'[^\wçğıöşüÇĞİÖŞÜ ]', ' ', s[:200].lower())
    for k, v in COUNTRIES.items():
        if re.search(r'(^|\W)' + re.escape(k) + r'($|\W)', head):
            cc_hits.append(v)
    line_country = cc_hits[0] if cc_hits else ''
    first = EMAIL_RE.search(s).start()
    pre = s[:first]
    pre = re.sub(r'[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u20E3]', ' ', pre)
    pre = re.sub(r'\s+', ' ', pre).strip(' :-–—|,.')
    records.append({'raw': s, 'name_pre': pre, 'emails': emails, 'country': line_country})

print('segments with emails:', len(records))
json.dump(records, open('work/records.json','w'), ensure_ascii=False)
