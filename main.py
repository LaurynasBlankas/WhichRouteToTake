from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()
gemini_api = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

start = json.loads(os.getenv("STARTPOINT"))
end = json.loads(os.getenv("ENDPOINT"))

via_gelezinio = [54.67289742078834, 25.239826325151537]
via_olandu = [54.692477785393024, 25.305084347042996]

def get_route(via_point):
    start_str = f"{start[0]},{start[1]}"
    via_str   = f"{via_point[0]},{via_point[1]}"
    end_str   = f"{end[0]},{end[1]}"

    url = f"https://api.tomtom.com/routing/1/calculateRoute/{start_str}:{via_str}:{end_str}/json"

    params = {
        "key": os.getenv("TOMTOM_API_KEY"),
        "traffic": "true",
        "travelMode": "car",
        "routeType": "fastest"
    }

    response = requests.get(url, params=params)
    data = response.json()
    summary = data["routes"][0]["summary"]

    return {
        "duration_min": round(summary["travelTimeInSeconds"] / 60, 1),
        "distance_km":  round(summary["lengthInMeters"] / 1000, 2)
    }

async def build_route_message():
    route_gelezinio = get_route(via_gelezinio)
    route_olandu    = get_route(via_olandu)

    prompt = f"""
    I need to drive from Vyturių 15, Kuprioniškės to SMK Vilnius.
    I have two route options with live traffic data:

    Route 1 - via Geležinio Vilko g:
    - Duration: {route_gelezinio['duration_min']} minutes
    - Distance: {route_gelezinio['distance_km']} km

    Route 2 - via Olandų g:
    - Duration: {route_olandu['duration_min']} minutes
    - Distance: {route_olandu['distance_km']} km

    Which route do you recommend and why (4 mins difference doesn't matter much if the route is shorter)? Be concise, 2-3 sentences max.
    """

    response = gemini_api.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return (
        f"🚗 *Route Check*\n\n"
        f"📍 *Geležinio Vilko g:* {route_gelezinio['duration_min']} min, {route_gelezinio['distance_km']} km\n"
        f"📍 *Olandų g:* {route_olandu['duration_min']} min, {route_olandu['distance_km']} km\n\n"
        f"🤖 *Gemini says:*\n{response.text}"
    )

async def check_route(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Checking routes with live traffic, please wait...")
    reply = await build_route_message()
    await update.message.reply_text(reply, parse_mode="Markdown")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm your commute assistant.\n\n"
        "Send /route to check live traffic for your morning drive.\n"
        "I'll also message you automatically at 8:20 AM every day!"
    )

async def morning_update(context: ContextTypes.DEFAULT_TYPE):
    reply = await build_route_message()
    await context.bot.send_message(chat_id=CHAT_ID, text=reply, parse_mode="Markdown")

async def post_init(application):
    # runs at 8:20 AM Lithuania time (UTC+3 = 05:20 UTC)
    application.job_queue.run_daily(
        morning_update,
        time=__import__("datetime").time(5, 20, tzinfo=__import__("datetime").timezone.utc),
        days=(0, 1, 2, 3)
    )

app = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN")).post_init(post_init).build()
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("route", check_route))

print("Bot is running...")
app.run_polling()