// Crescent Star Marine — Main Engine PLC & HMI budgetary quotation (TR + EN)
import { createRequire } from 'module';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

// Uses the repo's playwright dependency if installed, else the global one (npm root -g)
let chromium;
try { ({ chromium } = createRequire(import.meta.url)('playwright')); }
catch { ({ chromium } = createRequire(execSync('npm root -g').toString().trim() + '/')('playwright')); }
const DIR = path.dirname(fileURLToPath(import.meta.url));

const REF = 'CSM-ME-PLC-2026-0928';
const img = (n) => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(DIR, 'img', `p${n}.jpg`)).toString('base64');

const BUDGET = [45000, 75000]; // USD, excl. VAT
const CUSTOMER = 'Azimut Shipping';
const VESSEL = 'October 29';

const T = {
  tr: {
    lang: 'tr', file: 'CSM_Ana_Makine_PLC_HMI_On_Teklif_TR',
    fmt: (n) => n.toLocaleString('de-DE'),
    kicker: 'CRESCENT STAR MARINE',
    title: 'Ana Makine PLC & HMI<br>Alarm İzleme Sistemi',
    subtitle: 'Ön Fiyat Teklifi — Bilgilendirme Formatı',
    meta: [['Teklif No', REF], ['Tarih', '28.09.2026'], ['Müşteri', CUSTOMER], ['Gemi', VESSEL],
      ['Hazırlayan', 'Şükrü Umut Sanlı — Teknik Departman Direktörü'], ['Para Birimi', 'USD (ABD Doları)']],
    noticeH: 'Önemli Bilgilendirme',
    notice: 'Bu doküman <b>bilgilendirme amaçlı bir ön tekliftir, final teklif değildir.</b> Belirtilen fiyat aralığı, <b>sizin istekleriniz doğrultusunda</b> ve sistem kapsamına göre değişiklik gösterecektir. Nihai fiyat; gemide yapılacak keşif ve kapsamın netleştirilmesinin ardından final teklif ile bildirilecektir.',
    dear: `Sayın ${CUSTOMER} Yetkilileri,`,
    intro: `${VESSEL} gemisinin ana makinesine yönelik PLC tabanlı alarm, izleme ve kontrol sisteminin (PLC + HMI) tasarımı, pano imalatı, yazılımı ve devreye alınması için hazırladığımız ön fiyat bilgilendirmesini bilgilerinize sunarız. Önerilen sistem; Siemens SIMATIC PLC altyapısı, makine kontrol odası (ECR) dokunmatik HMI panelleri ve çift monitörlü SCADA iş istasyonundan oluşmaktadır.`,
    stats: [['Tahmini Bütçe', '45.000 – 75.000 USD', 'KDV hariç'], ['Platform', 'Siemens SIMATIC', 'PLC + dokunmatik HMI'], ['Kapsam', 'Ana Makine + Yardımcılar', 'G/B, DG, pompalar, tanklar…']],
    heroCap: 'ECR SCADA iş istasyonu — ana makine mimik ekranı (sol) ve jeneratör DG1 alarm sayfası (sağ). Örnek sistem ekranı.',
    s1: 'Sistem Ekranları', s1k: 'ÖRNEK ARAYÜZLER',
    shots: [[4, 'M/E Mimik', '9 silindir egzoz sıcaklıkları ve ortalamadan sapma, T/C çıkış, yağ / yakıt / soğutma suyu basınç ve sıcaklıkları, şaft yatağı ve G/B değerleri.'],
      [2, 'M/E Alarm Paneli', 'Gruplandırılmış dijital alarm noktaları, aktif alarmların renkli gösterimi, ACK / Horn Stop ve sistem grubu navigasyonu.'],
      [3, 'Aktif Alarm Listesi', 'Tarih ve saat damgalı alarm kaydı; egzoz sapmaları, sargı sıcaklıkları, basınç ve seviye alarmları.'],
      [5, 'Analog Alarm Ayarları', 'Her kanal için alt / üst limit, alarm gecikmesi (sn) ve alarm cut-off — yetkili personel tarafından ayarlanabilir.']],
    shotsNote: 'Görseller örnek sistem ekranlarıdır. Ekran tasarımları, geminin I/O listesi ve talepleriniz doğrultusunda uyarlanır.',
    s2: 'Teklif Kapsamı', s2k: 'NELER DAHİL',
    scope: [['Mühendislik & Tasarım', 'Mevcut sistem ve I/O keşfi, I/O listesi, elektrik ve pano şemaları, fonksiyonel tanımlama, klas onay dokümantasyonu.'],
      ['PLC Donanımı', 'Siemens SIMATIC S7 CPU, dijital / analog giriş-çıkış, PT100 / termokupl modülleri, güç kaynakları ve UPS.'],
      ['HMI Panelleri', 'SIMATIC dokunmatik HMI panel(ler) — ECR, lokal ve/veya köprüüstü (talebe göre).'],
      ['ECR SCADA İstasyonu', 'Endüstriyel PC, çift monitör, mimik ekranlar, alarm log ve kayıt ekranları.'],
      ['Pano İmalatı', 'Denizcilik tipi PLC panosu; klemens, röle, sigorta, iç kablolama ve pano sıcaklık izleme.'],
      ['Yazılım', 'PLC & HMI programlama; M/E, pompa, tank, sintine, G/B, seperatör, baş itici, kazan ve DG alarm grupları; ACK, Horn Stop, Deadman.'],
      ['Devreye Alma & Test', 'Montaj süpervizyonu, loop testleri, FAT / SAT, klas sörveyi sırasında destek.'],
      ['Eğitim & Dokümantasyon', 'Personel eğitimi, as-built çizimler, kullanım kılavuzu ve program yedekleri.']],
    s3: 'Fiyatlandırma', s3k: 'TAHMİNİ BÜTÇE',
    total: 'Toplam Tahmini Bütçe', totalNote: 'KDV hariç',
    priceNote: 'Belirtilen aralık, Bölüm 2’deki teklif kapsamını içerir. Fiyatlar, sizin istekleriniz doğrultusunda değişiklik gösterecek olup nihai fiyat final teklifte belirlenecektir.',
    s4: 'Fiyata Dahil Olmayanlar',
    excl: ['Değiştirilmesi gereken <b>sensörler</b>, transmitterler, sıcaklık elemanları (PT100 / termokupl), basınç ve seviye şalterleri gibi saha ekipmanları (varsa).',
      'Değiştirilmesi / yenilenmesi gereken <b>kablolar</b> (varsa).',
      '<b>KDV</b> — fiyatlara KDV dahil değildir.'],
    s5: 'Fiyatı Belirleyen Faktörler',
    factors: ['İzlenecek toplam I/O (dijital / analog) nokta sayısı', 'HMI panel adedi ve konumları (ECR, köprüüstü, lokal)', 'SCADA iş istasyonu ve monitör sayısı', 'Sisteme dahil edilecek yardımcı sistemler', 'Yedeklilik talepleri (CPU, ağ, güç kaynağı)', 'Klas kuruluşu gereklilikleri ve onay süreci', 'Mevcut sistemden yeniden kullanılacak ekipman', 'Uzaktan izleme / veri kaydı gibi ek özellikler'],
    s6: 'Sonraki Adımlar',
    steps: [['Keşif', 'Gemide mevcut sistemin incelenmesi ve I/O listesinin çıkarılması'], ['Kapsam', 'Talepleriniz doğrultusunda sistem kapsamının birlikte netleştirilmesi'], ['Final Teklif', 'Kesin fiyat, teslim süresi ve ödeme koşullarının iletilmesi']],
    closing: 'Her türlü soru ve talebiniz için bizimle iletişime geçebilirsiniz. Keşif planlaması için uygun tarihlerinizi bekleriz.',
    regards: 'Saygılarımızla,',
    role: 'Teknik Departman Direktörü',
    footer: 'Ön teklif — final teklif değildir · Fiyatlara KDV dahil değildir', page: 'Sayfa',
  },
  en: {
    lang: 'en', file: 'CSM_Main_Engine_PLC_HMI_Budgetary_Quotation_EN',
    fmt: (n) => n.toLocaleString('en-US'),
    kicker: 'CRESCENT STAR MARINE',
    title: 'Main Engine PLC & HMI<br>Alarm Monitoring System',
    subtitle: 'Budgetary Quotation — For Information Only',
    meta: [['Quotation No', REF], ['Date', '28 Sep 2026'], ['Customer', CUSTOMER], ['Vessel', VESSEL],
      ['Prepared by', 'Şükrü Umut Sanlı — Technical Department Director'], ['Currency', 'USD (US Dollar)']],
    noticeH: 'Important Notice',
    notice: 'This document is a <b>budgetary quotation for information purposes only and is not a final offer.</b> The price range stated will vary <b>according to your requirements</b> and the final system scope. The final price will be submitted in a formal quotation after an on-board survey and scope confirmation.',
    dear: `Dear ${CUSTOMER} Team,`,
    intro: `Please find below our budgetary pricing for the design, cabinet manufacturing, software and commissioning of a PLC-based alarm, monitoring and control system (PLC + HMI) for the main engine of your vessel ${VESSEL}. The proposed system is built on Siemens SIMATIC PLC hardware, touch-screen HMI panels in the engine control room (ECR) and a dual-monitor SCADA workstation.`,
    stats: [['Estimated Budget', 'USD 45,000 – 75,000', 'excluding VAT'], ['Platform', 'Siemens SIMATIC', 'PLC + touch HMI'], ['Scope', 'Main Engine + Auxiliaries', 'G/B, DG, pumps, tanks…']],
    heroCap: 'ECR SCADA workstation — main engine mimic (left) and generator DG1 alarm page (right). Example system screens.',
    s1: 'System Screens', s1k: 'EXAMPLE INTERFACES',
    shots: [[4, 'M/E Mimic', 'Exhaust gas temperatures for all 9 cylinders with deviation from average, T/C outlet, LO / FO / cooling water pressures and temperatures, shaft bearing and G/B values.'],
      [2, 'M/E Alarm Panel', 'Grouped digital alarm points, colour-coded active alarms, ACK / Horn Stop and system group navigation.'],
      [3, 'Active Alarm List', 'Date and time-stamped alarm log: exhaust deviations, winding temperatures, pressure and level alarms.'],
      [5, 'Analog Alarm Settings', 'Low / high limits, alarm delay (s) and alarm cut-off per channel — adjustable by authorised personnel.']],
    shotsNote: 'Images show example system screens. Screen layouts are adapted to the vessel’s I/O list and your requirements.',
    s2: 'Scope of Supply', s2k: 'WHAT IS INCLUDED',
    scope: [['Engineering & Design', 'Survey of existing system and I/O, I/O list, electrical and cabinet drawings, functional description, class approval documents.'],
      ['PLC Hardware', 'Siemens SIMATIC S7 CPU, digital / analog I/O, PT100 / thermocouple modules, power supplies and UPS.'],
      ['HMI Panels', 'SIMATIC touch HMI panel(s) — ECR, local and/or bridge (as requested).'],
      ['ECR SCADA Station', 'Industrial PC, dual monitors, mimic pages, alarm log and history screens.'],
      ['Cabinet Manufacturing', 'Marine-type PLC cabinet with terminals, relays, fuses, internal wiring and cabinet temperature monitoring.'],
      ['Software', 'PLC & HMI programming; M/E, pumps, tanks, bilge, G/B, purifier, bow thruster, boiler and DG alarm groups; ACK, Horn Stop, Deadman.'],
      ['Commissioning & Testing', 'Installation supervision, loop tests, FAT / SAT, support during class survey.'],
      ['Training & Documentation', 'Crew training, as-built drawings, operating manual and program backups.']],
    s3: 'Pricing', s3k: 'ESTIMATED BUDGET',
    total: 'Total Estimated Budget', totalNote: 'excluding VAT',
    priceNote: 'The stated range covers the scope of supply in Section 2. Prices will vary according to your requirements; the final price will be confirmed in the final quotation.',
    s4: 'Not Included in the Price',
    excl: ['Any <b>sensors</b>, transmitters, temperature elements (PT100 / thermocouple), pressure and level switches or other field equipment that need replacing.',
      'Any <b>cables</b> that need replacing / renewing.',
      '<b>VAT</b> — prices exclude VAT.'],
    s5: 'What Determines the Price',
    factors: ['Total number of monitored I/O points (digital / analog)', 'Number and location of HMI panels (ECR, bridge, local)', 'Number of SCADA workstations and monitors', 'Auxiliary systems to be integrated', 'Redundancy requirements (CPU, network, power supply)', 'Classification society requirements and approval', 'Existing equipment to be reused', 'Extras such as remote monitoring / data logging'],
    s6: 'Next Steps',
    steps: [['Survey', 'On-board inspection of the existing system and preparation of the I/O list'], ['Scope', 'Confirming the system scope together, according to your requirements'], ['Final Quotation', 'Submission of firm price, delivery time and payment terms']],
    closing: 'Please do not hesitate to contact us with any questions. We look forward to hearing your preferred dates for the on-board survey.',
    regards: 'Best regards,',
    role: 'Technical Department Director',
    footer: 'Budgetary quotation — not a final offer · Prices exclude VAT', page: 'Page',
  },
};

const emblem = (size) => `<svg width="${size}" height="${size}" viewBox="0 0 100 100" aria-hidden="true">
  <circle cx="50" cy="50" r="48" fill="#F4A11C"/>
  <g fill="none" stroke="#0B2A4A" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round">
    <path d="M46 26h8v8h-8z"/><path d="M36 34h28v14H36z"/><path d="M42 40h4M54 40h4"/>
    <path d="M26 50l24-6 24 6-5 14H31z"/><path d="M50 44v20"/>
    <path d="M24 72q6.5-5 13 0t13 0 13 0 13 0"/></g></svg>`;

const check = `<svg viewBox="0 0 20 20" width="12" height="12"><path d="M4 10.5l4 4 8-9" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const cross = `<svg viewBox="0 0 20 20" width="11" height="11"><path d="M5 5l10 10M15 5L5 15" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/></svg>`;

function html(t) {
  const range = (p) => `${t.fmt(p[0])} – ${t.fmt(p[1])}`;
  return `<!doctype html><html lang="${t.lang}"><head><meta charset="utf-8"><title>Crescent Star Marine — ${REF}</title>
<style>
:root{--navy:#0B2A4A;--navy2:#12335A;--panel:#143A63;--orange:#F4A11C;--teal:#1C7293;--ink:#1B2733;--muted:#5C6B7A;--line:#DCE4EC;--bg:#F1F5F9;--pale:#D8E6F0}
@page{size:A4;margin:14mm 0 16mm}
@page:first{margin-top:0}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font-family:'Carlito',sans-serif;color:var(--ink);font-size:10.5pt;line-height:1.45;background:#fff}
h1,h2,h3{font-family:'URW Bookman',serif;font-weight:600;margin:0;color:var(--navy)}
.wrap{padding:0 16mm}
.band{background:var(--navy);color:#fff;display:flex;align-items:stretch}
.band .l{flex:1;padding:13mm 10mm 11mm 16mm}
.band .r{width:52mm;background:var(--panel);display:flex;align-items:center;justify-content:center}
.kicker{font-weight:700;letter-spacing:3.2px;font-size:8.5pt;color:var(--orange)}
.band h1{color:#fff;font-size:23pt;line-height:1.15;margin:4mm 0 3mm}
.band .sub{font-family:'URW Bookman',serif;font-style:italic;font-weight:300;color:var(--orange);font-size:12.5pt}
.meta{display:grid;grid-template-columns:1fr 1fr;gap:0 10mm;margin:7mm 0 5mm;border-top:2px solid var(--navy)}
.meta div{display:flex;padding:2mm 0;border-bottom:1px solid var(--line);font-size:10pt}
.meta b{width:27mm;flex:none;color:var(--teal);font-size:8pt;letter-spacing:1px;text-transform:uppercase;padding-top:1px}
.fill{display:inline-block;width:52mm;border-bottom:1px dotted #9AA8B6;height:1em}
.notice{background:#FFF6E6;border-left:4px solid var(--orange);padding:3.2mm 4.5mm;border-radius:0 6px 6px 0;font-size:10pt}
.notice h3{font-family:'Carlito';font-weight:700;font-size:8.5pt;letter-spacing:1.6px;text-transform:uppercase;color:#B06E00;margin-bottom:1mm}
p{margin:0 0 2.5mm}
.dear{margin-top:5mm;font-weight:700}
.stats{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:3.5mm;margin:5mm 0}
.stat{background:var(--bg);border-radius:6px;padding:3.5mm 4mm;border-top:3px solid var(--teal)}
.stat:first-child{background:var(--navy);border-top-color:var(--orange)}
.stat .k{font-size:7.5pt;letter-spacing:1.4px;text-transform:uppercase;color:var(--teal);font-weight:700}
.stat .v{font-family:'URW Bookman',serif;font-weight:600;font-size:12.5pt;color:var(--navy);margin:1mm 0 .5mm;white-space:nowrap}
.stat .n{font-size:8.5pt;color:var(--muted)}
.stat:first-child .k,.stat:first-child .n{color:var(--orange)}
.stat:first-child .v{color:#fff;font-size:13.5pt}
figure{margin:0}
.hero img{width:100%;display:block;border-radius:6px}
figcaption{font-size:8.5pt;color:var(--muted);margin-top:1.5mm;font-style:italic}
.sec{margin-top:5mm}
.sk{font-weight:700;letter-spacing:2.6px;font-size:7.5pt;color:var(--teal)}
.sec h2{font-size:16pt;margin:1mm 0 3mm;display:flex;align-items:center;gap:3mm}
.sec h2 .num{width:8mm;height:8mm;border-radius:50%;background:var(--orange);color:var(--navy);font-size:10.5pt;display:inline-flex;align-items:center;justify-content:center;flex:none}
.pb{break-before:page}
.shots{display:grid;grid-template-columns:1fr 1fr;gap:3mm}
.shot{border:1px solid var(--line);border-radius:6px;overflow:hidden;break-inside:avoid;background:#fff}
.shot img{width:100%;height:37mm;object-fit:cover;display:block}
.shot .c{padding:2mm 3.5mm 2.4mm}
.shot h3{font-family:'Carlito';font-weight:700;font-size:10.5pt}
.shot p{font-size:8.8pt;color:var(--muted);margin:.5mm 0 0;line-height:1.35}
.note{font-size:8.5pt;color:var(--muted);font-style:italic;margin-top:2.5mm}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:2.5mm}
.card{display:flex;gap:3mm;background:var(--bg);border-radius:6px;padding:2.3mm 3.2mm;break-inside:avoid}
.card .i{width:7mm;height:7mm;border-radius:50%;background:var(--teal);display:flex;align-items:center;justify-content:center;flex:none;margin-top:.5mm}
.card h3{font-family:'Carlito';font-weight:700;font-size:10.5pt;color:var(--navy)}
.card p{font-size:8.8pt;color:var(--muted);margin:.3mm 0 0;line-height:1.35}
.total{display:flex;align-items:center;justify-content:space-between;background:var(--navy);color:#fff;border-radius:6px;border-left:5px solid var(--orange);padding:6mm 7mm}
.total .k{font-family:'URW Bookman',serif;font-weight:600;font-size:14pt}
.total .v{text-align:right}
.total .v b{display:block;font-family:'URW Bookman',serif;font-weight:600;font-size:22pt;color:var(--orange);white-space:nowrap}
.total .v span{font-size:8.5pt;letter-spacing:1.4px;text-transform:uppercase;color:var(--pale)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:6mm}
ul.x,ul.f{list-style:none;margin:0;padding:0}
ul.x li{display:flex;gap:2.5mm;padding:1.3mm 0;border-bottom:1px solid var(--line);font-size:9.6pt;line-height:1.35}
ul.x li .i{width:5.5mm;height:5.5mm;border-radius:50%;background:#C0392B;display:flex;align-items:center;justify-content:center;flex:none;margin-top:.3mm}
ul.f li{position:relative;padding:.45mm 0 .45mm 5mm;font-size:9.6pt;line-height:1.35}
ul.f li:before{content:'';position:absolute;left:0;top:2.2mm;width:2.2mm;height:2.2mm;background:var(--orange);border-radius:1px;transform:rotate(45deg)}
.sec h2.sm{font-size:13pt;margin-bottom:2mm}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:3mm;break-inside:avoid}
.step{background:var(--bg);border-radius:6px;padding:2.6mm 3.5mm;position:relative}
.step .no{font-family:'URW Bookman',serif;font-weight:600;font-size:13pt;color:var(--orange);line-height:1;margin-right:2mm}
.step .hd{display:flex;align-items:baseline}
.step h3{font-family:'Carlito';font-weight:700;font-size:10.5pt;margin:0 0 .6mm}
.step p{font-size:8.8pt;color:var(--muted);margin:0;line-height:1.35}
.sign{display:flex;align-items:stretch;margin-top:3mm;border-radius:6px;overflow:hidden;break-inside:avoid;background:var(--navy);color:#fff}
.sign .e{padding:3mm 4.5mm;display:flex;align-items:center;background:var(--panel)}
.sign .b{flex:1;padding:2.8mm 5mm}
.sign .nm{font-family:'URW Bookman',serif;font-weight:600;font-size:13pt}
.sign .ro{color:var(--pale);font-size:9pt}
.sign .co{font-weight:700;letter-spacing:2.4px;font-size:8.5pt;color:var(--orange);margin-top:1mm}
.sign .ct{display:grid;grid-template-columns:auto auto;gap:.2mm 5mm;margin-top:1.5mm;font-size:9pt;color:var(--pale)}
.sign .ct b{color:var(--orange);margin-right:1.5mm}
.sign .q{align-self:flex-end;width:38mm;text-align:right;padding:3.5mm 5mm 3.5mm 0;font-family:'URW Bookman',serif;font-style:italic;font-weight:600;color:var(--orange);font-size:9.5pt;line-height:1.3}
</style></head><body>

<header class="band">
  <div class="l"><div class="kicker">${t.kicker}</div><h1>${t.title}</h1><div class="sub">${t.subtitle}</div></div>
  <div class="r">${emblem(118)}</div>
</header>

<div class="wrap">
  <div class="meta">${t.meta.map(([k, v]) => `<div><b>${k}</b><span>${v}</span></div>`).join('')}</div>
  <div class="notice"><h3>${t.noticeH}</h3>${t.notice}</div>

  <p class="dear">${t.dear}</p>
  <p>${t.intro}</p>

  <div class="stats">${t.stats.map(([k, v, n]) => `<div class="stat"><div class="k">${k}</div><div class="v">${v}</div><div class="n">${n}</div></div>`).join('')}</div>

  <figure class="hero"><img src="${img(1)}" alt=""><figcaption>${t.heroCap}</figcaption></figure>

  <section class="sec pb">
    <div class="sk">${t.s1k}</div><h2><span class="num">1</span>${t.s1}</h2>
    <div class="shots">${t.shots.map(([n, h, d]) => `<figure class="shot"><img src="${img(n)}" alt=""><div class="c"><h3>${h}</h3><p>${d}</p></div></figure>`).join('')}</div>
    <div class="note">${t.shotsNote}</div>
  </section>

  <section class="sec">
    <div class="sk">${t.s2k}</div><h2><span class="num">2</span>${t.s2}</h2>
    <div class="cards">${t.scope.map(([h, d]) => `<div class="card"><div class="i">${check}</div><div><h3>${h}</h3><p>${d}</p></div></div>`).join('')}</div>
  </section>

  <section class="sec pb">
    <div class="sk">${t.s3k}</div><h2><span class="num">3</span>${t.s3}</h2>
    <div class="total"><div class="k">${t.total}</div><div class="v"><b>${range(BUDGET)} USD</b><span>${t.totalNote}</span></div></div>
    <div class="note">${t.priceNote}</div>
  </section>

  <div class="two">
    <section class="sec"><h2 class="sm"><span class="num">4</span>${t.s4}</h2>
      <ul class="x">${t.excl.map((e) => `<li><span class="i">${cross}</span><span>${e}</span></li>`).join('')}</ul></section>
    <section class="sec"><h2 class="sm"><span class="num">5</span>${t.s5}</h2>
      <ul class="f">${t.factors.map((f) => `<li>${f}</li>`).join('')}</ul></section>
  </div>

  <section class="sec">
    <h2 class="sm"><span class="num">6</span>${t.s6}</h2>
    <div class="steps">${t.steps.map(([h, d], i) => `<div class="step"><div class="hd"><span class="no">0${i + 1}</span><h3>${h}</h3></div><p>${d}</p></div>`).join('')}</div>
  </section>

  <p style="margin-top:3.5mm;margin-bottom:0">${t.closing}<br>${t.regards}</p>
  <div class="sign">
    <div class="e">${emblem(50)}</div>
    <div class="b"><div class="nm">Şükrü Umut Sanlı</div><div class="ro">${t.role}</div><div class="co">CRESCENT STAR MARINE</div>
      <div class="ct"><span><b>T</b>+90 535 044 82 50</span><span><b>W</b>www.crescentstarmarine.com</span><span><b>E</b>umut.sanli@crescentstarmarine.com</span><span><b>A</b>Kadıköy, İstanbul — Türkiye</span></div></div>
    <div class="q">“Your Ship is Our Business.”</div>
  </div>
</div>
</body></html>`;
}

const footer = (t) => `<div style="width:100%;font-family:Carlito,sans-serif;font-size:7.5pt;color:#5C6B7A;padding:0 16mm;display:flex;justify-content:space-between;align-items:center;-webkit-print-color-adjust:exact">
  <span><b style="color:#0B2A4A;letter-spacing:1.5px">CRESCENT STAR MARINE</b> &nbsp;·&nbsp; ${REF}</span>
  <span>${t.footer}</span>
  <span>${t.page} <span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`;

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
const page = await browser.newPage();
for (const t of Object.values(T)) {
  const h = html(t);
    await page.setContent(h, { waitUntil: 'load' });
  await page.pdf({ path: path.join(DIR, `${t.file}.pdf`), preferCSSPageSize: true, printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: footer(t) });
  console.log('wrote', t.file);
}
await browser.close();
