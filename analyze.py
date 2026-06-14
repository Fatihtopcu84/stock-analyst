import yfinance as yf
import pandas as pd
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import os

STOCKS = {
    "TSLA": "Tesla Inc.",
    "NVDA": "NVIDIA Corp.",
    "NOVN.SW": "Novartis AG"
}

EMAIL_FROM = os.environ["EMAIL_FROM"]
EMAIL_TO   = os.environ["EMAIL_TO"]
EMAIL_PASS = os.environ["EMAIL_PASS"]


def compute_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss
    return 100 - (100 / (1 + rs))


def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast   = compute_ema(series, fast)
    ema_slow   = compute_ema(series, slow)
    macd_line  = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    return macd_line, signal_line


def signal_badge(val, reverse=False):
    """Return (text, color) tuple for a signal value."""
    if reverse:
        val = -val
    if val > 0:
        return "AL 🟢", "#16a34a"
    elif val < 0:
        return "SAT 🔴", "#dc2626"
    return "NÖTR ⚪", "#6b7280"


def pct_color(pct):
    return "#16a34a" if pct >= 0 else "#dc2626"


def analyze(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
    if df.empty:
        return None

    close = df["Close"].squeeze()
    price = float(close.iloc[-1])

    sma21  = float(close.rolling(21).mean().iloc[-1])
    sma50  = float(close.rolling(50).mean().iloc[-1])
    sma200 = float(close.rolling(200).mean().iloc[-1])

    ema21  = float(compute_ema(close, 21).iloc[-1])
    ema50  = float(compute_ema(close, 50).iloc[-1])
    ema200 = float(compute_ema(close, 200).iloc[-1])

    rsi = float(compute_rsi(close).iloc[-1])
    macd_line, signal_line = compute_macd(close)
    macd_val    = float(macd_line.iloc[-1])
    signal_val  = float(signal_line.iloc[-1])
    macd_cross  = macd_val - signal_val

    hi52 = float(close.rolling(252).max().iloc[-1])
    lo52 = float(close.rolling(252).min().iloc[-1])

    return {
        "ticker": ticker,
        "price": price,
        "sma21": sma21,  "ema21": ema21,
        "sma50": sma50,  "ema50": ema50,
        "sma200": sma200,"ema200": ema200,
        "rsi": rsi,
        "macd": macd_val,
        "macd_signal": signal_val,
        "macd_cross": macd_cross,
        "hi52": hi52,
        "lo52": lo52,
    }


def ma_row(label, price, ma_val):
    diff    = price - ma_val
    pct     = (diff / ma_val) * 100
    sig_txt, sig_color = signal_badge(diff)
    color   = pct_color(pct)
    arrow   = "▲" if diff >= 0 else "▼"
    return f"""
    <tr>
      <td style="padding:8px 12px;font-weight:500;">{label}</td>
      <td style="padding:8px 12px;text-align:right;">${ma_val:,.2f}</td>
      <td style="padding:8px 12px;text-align:right;color:{color};">{arrow} {abs(diff):,.2f}</td>
      <td style="padding:8px 12px;text-align:right;color:{color};">{arrow} {abs(pct):.2f}%</td>
      <td style="padding:8px 12px;text-align:center;">
        <span style="background:{sig_color}20;color:{sig_color};padding:2px 10px;border-radius:6px;font-size:12px;font-weight:600;">{sig_txt}</span>
      </td>
    </tr>"""


def stock_block(data, name):
    p = data["price"]

    rsi_color = "#16a34a" if 40 < data["rsi"] < 70 else "#dc2626"
    macd_txt, macd_color = signal_badge(data["macd_cross"])

    pct_52hi = (p - data["hi52"]) / data["hi52"] * 100
    pct_52lo = (p - data["lo52"]) / data["lo52"] * 100

    # overall: count buy signals from 6 MA levels
    buy_count = sum([
        data["price"] > data["sma21"],
        data["price"] > data["sma50"],
        data["price"] > data["sma200"],
        data["price"] > data["ema21"],
        data["price"] > data["ema50"],
        data["price"] > data["ema200"],
        data["macd_cross"] > 0,
        data["rsi"] > 50,
    ])
    if buy_count >= 6:
        overall_txt, overall_color = "GÜÇLÜ AL 🟢🟢", "#16a34a"
    elif buy_count >= 4:
        overall_txt, overall_color = "AL 🟢", "#16a34a"
    elif buy_count >= 3:
        overall_txt, overall_color = "NÖTR ⚪", "#6b7280"
    else:
        overall_txt, overall_color = "SAT 🔴", "#dc2626"

    return f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
    <div>
      <span style="font-size:20px;font-weight:700;color:#111827;">{data['ticker']}</span>
      <span style="font-size:14px;color:#6b7280;margin-left:8px;">{name}</span>
    </div>
    <div style="text-align:right;">
      <div style="font-size:22px;font-weight:700;color:#111827;">${p:,.2f}</div>
      <span style="background:{overall_color}20;color:{overall_color};padding:3px 14px;border-radius:8px;font-size:13px;font-weight:700;">{overall_txt}</span>
    </div>
  </div>

  <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:16px;">
    <thead>
      <tr style="background:#f9fafb;">
        <th style="padding:8px 12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Periyot</th>
        <th style="padding:8px 12px;text-align:right;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">SMA Değeri</th>
        <th style="padding:8px 12px;text-align:right;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Fark ($)</th>
        <th style="padding:8px 12px;text-align:right;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Uzaklık %</th>
        <th style="padding:8px 12px;text-align:center;font-weight:600;color:#374151;border-bottom:1px solid #e5e7eb;">Sinyal</th>
      </tr>
    </thead>
    <tbody style="color:#111827;">
      {ma_row("SMA 21 Gün", p, data['sma21'])}
      {ma_row("SMA 50 Gün", p, data['sma50'])}
      {ma_row("SMA 200 Gün", p, data['sma200'])}
      {ma_row("EMA 21 Gün", p, data['ema21'])}
      {ma_row("EMA 50 Gün", p, data['ema50'])}
      {ma_row("EMA 200 Gün", p, data['ema200'])}
    </tbody>
  </table>

  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <div style="flex:1;min-width:120px;background:#f9fafb;border-radius:8px;padding:10px 14px;">
      <div style="font-size:11px;color:#6b7280;margin-bottom:2px;">RSI (14)</div>
      <div style="font-size:18px;font-weight:600;color:{rsi_color};">{data['rsi']:.1f}</div>
    </div>
    <div style="flex:1;min-width:120px;background:#f9fafb;border-radius:8px;padding:10px 14px;">
      <div style="font-size:11px;color:#6b7280;margin-bottom:2px;">MACD Sinyali</div>
      <div style="font-size:13px;font-weight:600;color:{macd_color};">{macd_txt}</div>
    </div>
    <div style="flex:1;min-width:120px;background:#f9fafb;border-radius:8px;padding:10px 14px;">
      <div style="font-size:11px;color:#6b7280;margin-bottom:2px;">52H Tepe'ye</div>
      <div style="font-size:18px;font-weight:600;color:{pct_color(pct_52hi)};">{pct_52hi:.1f}%</div>
    </div>
    <div style="flex:1;min-width:120px;background:#f9fafb;border-radius:8px;padding:10px 14px;">
      <div style="font-size:11px;color:#6b7280;margin-bottom:2px;">52H Dip'ten</div>
      <div style="font-size:18px;font-weight:600;color:{pct_color(pct_52lo)};">+{pct_52lo:.1f}%</div>
    </div>
  </div>
</div>"""


def build_html(results):
    date_str = datetime.now().strftime("%d %B %Y — %H:%M")
    blocks   = "\n".join(stock_block(d, STOCKS[d["ticker"]]) for d in results)

    return f"""<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sabah Teknik Analiz Raporu</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:640px;margin:32px auto;padding:0 16px;">

  <div style="background:#111827;border-radius:12px;padding:20px 24px;margin-bottom:24px;color:#fff;">
    <div style="font-size:11px;letter-spacing:1px;color:#9ca3af;margin-bottom:4px;">SABAH RAPORU</div>
    <div style="font-size:22px;font-weight:700;">Teknik Analiz Bülteni</div>
    <div style="font-size:13px;color:#9ca3af;margin-top:4px;">{date_str} UTC</div>
  </div>

  {blocks}

  <div style="text-align:center;font-size:11px;color:#9ca3af;padding:16px 0 32px;">
    Bu rapor yatırım tavsiyesi değildir. Veri: Yahoo Finance (yfinance).<br>
    Hisseler: TSLA · NVDA · NOVN.SW
  </div>
</div>
</body></html>"""


def send_email(html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Sabah Teknik Analiz — {datetime.now().strftime('%d.%m.%Y')}"
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_FROM, EMAIL_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
    print("✅ E-posta gönderildi.")


def main():
    results = []
    for ticker, name in STOCKS.items():
        print(f"  ↓ {ticker} indiriliyor...")
        data = analyze(ticker)
        if data:
            results.append(data)
        else:
            print(f"  ⚠ {ticker} verisi alınamadı.")

    html = build_html(results)

    # dosya olarak da kaydet (opsiyonel)
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✅ report.html oluşturuldu.")

    send_email(html)


if __name__ == "__main__":
    main()
