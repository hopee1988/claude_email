# e_mail_ve_numaralar.docx → Excel doğrulama hattı

Çıktı: `denizcilik_firmalari_dogrulama.xlsx`

Akış:
1. `parse.py` – .docx metnini paragraflara ayırır, kayıt sınırlarını ve ülke başlıklarını bulur.
2. `extract3.py` – her e-posta için firma adı, telefon, bağlam metnini çıkarır.
3. `fixdom.py` – dokümanda bitişik yazılmış alan adlarını (ör. `...comnordic`) TLD sınırından düzeltir.
4. `group2.py` – kayıtları alan adına göre firma bazında gruplar (ücretsiz e-postalar ayrı tutulur).
5. `check.py` – her alan adı için https/http ana sayfa + iletişim/about sayfalarını canlı çeker, sayfalardaki e-postaları toplar.
6. `classify.py` / `build2.py` – owner/broker/acente/tersane vb. sınıflandırma, ülke tespiti, e-posta doğrulama durumu.
7. `xlsx.py` – Excel çıktısını üretir.
