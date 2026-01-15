import os
import json
import pytz
import discord
import datetime
import asyncio
from dotenv import load_dotenv

# ================== CONFIG ==================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

TARGET_TEXT_CHANNEL_ID = 123456789012345678
TARGET_VC_ID = 1356206346491400282

SOURCE_VC_IDS = [
    1238369263006388245,
    1082183176019005501,
    1301517898484813896,
    943130959421767707,
    977119532009291837,
    1000999038784647228,
    1028904893144125500,
    1203652885028802600,
    1095638837125988392,
    996669365527269386,
    1158370586989441115,
    1173231115075592323,
    1406969449214644346,
    1406969524330303538,
    1406969575488094329,
    1406969301864550430,
    1406969180447707247,
    1437671685657464894,
]

STATE_FILE = "state.json"
TZ = pytz.timezone("Asia/Almaty")

# ================== INTENTS ==================
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
user_original_channels = {}

# ================== STATE ==================
def load_state():
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

state = load_state()

# ================== EVENTS ==================
@client.event
async def on_ready():
    print(f"[+] Бот запущен как {client.user}")
    print("[~] Scheduler активирован")
    client.loop.create_task(workday_scheduler())

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "!status":
        last = state.get("last_run", "никогда")
        await message.channel.send(f"📊 Последний запуск: **{last}**")

    elif message.content.lower() == "!run_now":
        await message.channel.send("⚙️ Принудительный запуск задачи")
        await do_daily_task(force=True)

    elif message.content.lower() == "!shutdown":
        await message.channel.send("📦 Возвращаю пользователей и отключаюсь...")
        await return_users()
        await client.close()

# ================== SCHEDULER ==================
async def workday_scheduler():
    while True:
        now = datetime.datetime.now(TZ)
        target = now.replace(hour=11, minute=0, second=0, microsecond=0)

        if now >= target:
            target += datetime.timedelta(days=1)

        while target.weekday() >= 5:  # 5=Sat, 6=Sun
            target += datetime.timedelta(days=1)

        sleep_seconds = (target - now).total_seconds()
        print(f"[~] Следующий запуск: {target.strftime('%Y-%m-%d %H:%M')}")

        await asyncio.sleep(sleep_seconds)
        await do_daily_task()

# ================== TASK ==================
async def do_daily_task(force=False):
    today = datetime.datetime.now(TZ).strftime("%Y-%m-%d")

    if not force and state.get("last_run") == today:
        print("[!] Уже выполнялось сегодня — пропуск")
        return

    print(f"[✔] Выполнение задачи {today}")
    state["last_run"] = today
    save_state(state)

    for guild in client.guilds:
        target_vc = guild.get_channel(TARGET_VC_ID)
        text_channel = guild.get_channel(TARGET_TEXT_CHANNEL_ID)

        if not target_vc:
            print("[✘] Целевой VC не найден")
            continue

        if text_channel:
            await safe_send(text_channel, "🌞 Доброе утро, коллеги! Продуктивного дня 💪")

        for vc in guild.voice_channels:
            if vc.id not in SOURCE_VC_IDS:
                continue

            for member in vc.members:
                try:
                    user_original_channels[member.id] = vc.id
                    await member.move_to(target_vc)
                    print(f"[→] {member.display_name}")
                except discord.Forbidden:
                    print(f"[✘] Нет прав: {member.display_name}")
                except Exception as e:
                    print(f"[✘] Ошибка: {e}")

# ================== RETURN USERS ==================
async def return_users():
    for guild in client.guilds:
        members = [m async for m in guild.fetch_members(limit=None)]
        for member in members:
            if member.id in user_original_channels and member.voice:
                ch = guild.get_channel(user_original_channels[member.id])
                if ch:
                    try:
                        await member.move_to(ch)
                        print(f"[⏪] {member.display_name}")
                    except:
                        pass

# ================== UTILS ==================
async def safe_send(channel, text):
    try:
        await channel.send(text)
    except Exception as e:
        print(f"[✘] Не удалось отправить сообщение: {e}")

# ================== START ==================
if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
