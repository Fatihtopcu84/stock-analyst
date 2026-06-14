# 📊 Sabah Teknik Analiz Raporu

Her sabah **saat 06:00'da** (Türkiye saatiyle) TSLA, NVDA ve NOVN.SW hisselerinin teknik analizini otomatik olarak e-posta ile gönderir.

## Raporda neler var?

- SMA 21 / 50 / 200 günlük hareketli ortalama — fiyat uzaklığı ve sinyal
- EMA 21 / 50 / 200 günlük üssel hareketli ortalama
- RSI (14) göstergesi
- MACD sinyal çaprazlaması
- 52 haftalık tepe/dip uzaklığı
- Her hisse için AL / NÖTR / SAT kararı

---

## Kurulum (10 dakika)

### 1. Bu repoyu fork edin

GitHub'da sağ üstteki **Fork** butonuna tıklayın.

---

### 2. Gmail App Password alın

> Gmail 2FA açıksa normal şifre çalışmaz — App Password gerekli.

1. [myaccount.google.com/security](https://myaccount.google.com/security) adresine gidin
2. **2-Step Verification** → açık olduğundan emin olun
3. Arama kutusuna "App passwords" yazın
4. Uygulama: **Mail** / Cihaz: **Other (custom name)** → "GitHub Actions" yazın
5. **Generate** → 16 haneli şifre kopyalayın (`xxxx xxxx xxxx xxxx`)

---

### 3. GitHub Secrets ekleyin

Fork ettiğiniz repoda:
**Settings → Secrets and variables → Actions → New repository secret**

| Secret adı   | Değer                          |
|--------------|-------------------------------|
| `EMAIL_FROM` | gmail adresiniz@gmail.com     |
| `EMAIL_TO`   | rapor gönderilecek e-posta    |
| `EMAIL_PASS` | 2. adımda aldığınız 16h şifre |

---

### 4. Saati ayarlayın (isteğe bağlı)

`.github/workflows/morning_report.yml` dosyasındaki cron satırı:

```yaml
- cron: "0 3 * * 1-5"   # UTC 03:00 = Türkiye 06:00
```

| İstenen saat (TR) | Cron değeri         |
|-------------------|---------------------|
| 06:00             | `0 3 * * 1-5`       |
| 07:00             | `0 4 * * 1-5`       |
| 08:00             | `0 5 * * 1-5`       |
| Her gün (hf dahil)| `0 3 * * *`         |

---

### 5. Test edin

**Actions** sekmesi → **Sabah Teknik Analiz Raporu** → **Run workflow** → **Run workflow** butonuna tıklayın.

Birkaç saniye içinde e-postanız gelecek!

---

## Hisse eklemek / çıkarmak

`scripts/analyze.py` içindeki `STOCKS` sözlüğünü düzenleyin:

```python
STOCKS = {
    "TSLA":    "Tesla Inc.",
    "NVDA":    "NVIDIA Corp.",
    "NOVN.SW": "Novartis AG",
    "AAPL":    "Apple Inc.",      # eklemek için
}
```

Yahoo Finance ticker sembollerini kullanın.  
Türk hisseleri için örnek: `"THYAO.IS": "Türk Hava Yolları"`

---

## Sorun giderme

| Hata | Çözüm |
|------|-------|
| Authentication error | Gmail App Password doğru girildiğinden emin olun |
| Veri alınamadı | Ticker sembolü Yahoo Finance'de geçerli mi kontrol edin |
| E-posta gelmiyor | Spam klasörünü kontrol edin |

---

*Veriler Yahoo Finance üzerinden çekilir. Bu proje yatırım tavsiyesi vermez.*
