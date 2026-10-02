import os
import html
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(url, json=payload, timeout=10)
    return response


def format_signal(data):
    direction = str(data.get("direction", "")).upper()
    asset = str(data.get("asset", ""))
    ticker = str(data.get("ticker", ""))
    timeframe = str(data.get("timeframe", ""))

    entry = data.get("entry")
    sl = data.get("sl")
    tp1 = data.get("tp1")
    tp2 = data.get("tp2")
    tp3 = data.get("tp3")

    required = [direction, asset, ticker, entry, sl, tp1, tp2, tp3]

    if any(value in ("", None) for value in required):
        raise ValueError("Données TradingView incomplètes.")

    if direction == "LONG":
        emoji = "🟢"
    elif direction == "SHORT":
        emoji = "🔴"
    else:
        emoji = "⚪"

    message = (
        f"{emoji} <b>{html.escape(direction)}</b>\n"
        f"\n"
        f"<b>{html.escape(ticker)}</b> — {html.escape(asset)}\n"
        f"Timeframe : {html.escape(timeframe)}\n"
        f"\n"
        f"📍 <b>Entrée :</b> {html.escape(str(entry))}\n"
        f"🛑 <b>SL :</b> {html.escape(str(sl))}\n"
        f"🎯 <b>TP1 :</b> {html.escape(str(tp1))}\n"
        f"🎯 <b>TP2 :</b> {html.escape(str(tp2))}\n"
        f"🎯 <b>TP3 :</b> {html.escape(str(tp3))}"
    )

    return message


@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "error": "JSON TradingView manquant."
            }), 400

        print("Signal TradingView reçu :", data)

        message = format_signal(data)

        telegram_response = send_telegram(message)

        if telegram_response.status_code != 200:
            print(
                "Erreur Telegram :",
                telegram_response.status_code,
                telegram_response.text
            )

            return jsonify({
                "success": False,
                "error": "Telegram a refusé le message."
            }), 500

        print("Message Telegram envoyé.")

        return jsonify({
            "success": True,
            "message": "Signal envoyé sur Telegram."
        }), 200

    except Exception as error:
        print("Erreur :", error)

        return jsonify({
            "success": False,
            "error": str(error)
        }), 500


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "online",
        "service": "TradingView → Telegram",
        "webhook": "/webhook"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
