import sqlite3
import random
import tweepy
import os
import time
from datetime import datetime

# 📂 Database SQLite
db = sqlite3.connect("citazioni.db")
cursor = db.cursor()

# 🎲 Seleziona una citazione casuale
cursor.execute("SELECT testo, autore FROM calcio ORDER BY RANDOM() LIMIT 1;")
citazione = cursor.fetchone()
cursor.close()
db.close()

# Se non ci sono citazioni, esce
if not citazione:
    print("⚠️ Nessuna citazione trovata.")
    exit()

# 📜 Formatta il tweet
testo, autore = citazione
tweet_text = f"{testo}\n\n- {autore}"

# 🛑 Controlla il limite di 280 caratteri
if len(tweet_text) > 280:
    print("⚠️ Citazione troppo lunga, saltata.")
    exit()

# 🔑 Credenziali API Twitter (da variabili ambiente per sicurezza)
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_secret = os.getenv("ACCESS_SECRET")

if not all([api_key, api_secret, access_token, access_secret]):
    print("⚠️ Errore: Credenziali API mancanti.")
    exit()

# 📡 Connessione a Twitter API v2
client = tweepy.Client(
    consumer_key=api_key,
    consumer_secret=api_secret,
    access_token=access_token,
    access_token_secret=access_secret
)

# 🔄 Limite di 15 tweet al giorno
DAILY_LIMIT = 15
COUNTER_FILE = "tweet_counter.txt"

def get_tweet_count():
    """ Controlla quanti tweet sono stati pubblicati oggi. """
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            data = f.read().strip().split(",")
            if len(data) == 2:
                count, last_date = int(data[0]), data[1]
                today = datetime.now().strftime("%Y-%m-%d")
                if last_date != today:
                    return 0, today  # Resetta il contatore se è un nuovo giorno
                return count, last_date
    return 0, datetime.now().strftime("%Y-%m-%d")

def update_tweet_count(count, date):
    """ Aggiorna il file con il numero di tweet pubblicati oggi. """
    with open(COUNTER_FILE, "w") as f:
        f.write(f"{count},{date}")

daily_count, last_date = get_tweet_count()

def publish_tweet(text):
    """ Pubblica il tweet gestendo il rate limit. """
    global daily_count, last_date
    if daily_count >= DAILY_LIMIT:
        print(f"⚠️ Limite giornaliero raggiunto: {daily_count}/{DAILY_LIMIT}")
        return False
    try:
        response = client.create_tweet(text=text)
        daily_count += 1
        last_date = datetime.now().strftime("%Y-%m-%d")
        update_tweet_count(daily_count, last_date)
        print(f"✅ Tweet pubblicato! ID: {response.data['id']} ({daily_count}/{DAILY_LIMIT})")
        return True
    except tweepy.errors.TooManyRequests as e:
        headers = e.response.headers
        reset_time = int(headers.get('x-rate-limit-reset'))
        wait_seconds = reset_time - int(time.time())
        if wait_seconds > 0:
            reset_datetime = datetime.fromtimestamp(reset_time)
            print(f"⏳ 429 Too Many Requests: Attendo {wait_seconds} secondi fino a {reset_datetime}")
            time.sleep(wait_seconds)
            return publish_tweet(text)
        print("🔄 Reset passato, riprovo...")
        return publish_tweet(text)
    except Exception as e:
        print(f"❌ Errore durante la pubblicazione: {e}")
        return False

# 🚀 Prova a pubblicare il tweet
success = publish_tweet(tweet_text)
if not success:
    print("⚠️ Impossibile pubblicare ora.")
