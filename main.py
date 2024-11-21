import os
import asyncio
import requests
from dotenv import load_dotenv
import discord

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48
BINANCE_API_URL = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"
CHECK_INTERVAL = 30

last_article_id = None

async def send_to_discord(article, channel):
    base_url = "https://www.binance.com/en/support/announcement/"
    article_url = f"{base_url}{article['code']}"
    message_content = f"{article['title']}\n{article_url}"
    
    await channel.send(message_content)

def fetch_latest_articles():
    params = {"type": 1, "pageNo": 1, "pageSize": 5}
    response = requests.get(BINANCE_API_URL, params=params)
    response.raise_for_status()
    data = response.json()

    catalogs = data.get("data", {}).get("catalogs", [])
    for catalog in catalogs:
        if catalog.get("catalogName") == "New Cryptocurrency Listing":
            articles = catalog.get("articles", [])
            return [{"id": article["id"], "code": article["code"], "title": article["title"], "releaseDate": article["releaseDate"]} for article in articles]

    return []

async def monitor(channel):
    global last_article_id

    while True:
        try:
            articles = fetch_latest_articles()

            if not articles:
                print("No articles found. Retrying...")
                await asyncio.sleep(CHECK_INTERVAL)
                continue

            latest_article = articles[0]

            if last_article_id != latest_article["id"]:
                last_article_id = latest_article["id"]
                await send_to_discord(latest_article, channel)
                print(f"Sent notification for: {latest_article['title']}")
            else:
                print("No new articles.")
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"{client.user} is now online!")
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await monitor(channel)

client.run(TOKEN)
