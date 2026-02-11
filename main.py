import os
import pytz
import discord
import datetime
import asyncio

TOKEN = os.environ["DISCORD_TOKEN"]


TARGET_GUILD_ID = 111111111111111111  # <-- ID сервера

TARGET_TEXT_CHANNEL_ID = 1356206346491400282
TARGET_VC_ID = 1356206346491400282


SOURCE_VC_IDS = [
    1238369263006388245,  #Semey Room
    1082183176019005501,  #Damir-Bauka
    1301517898484813896,  #Dauytbek
    943130959421767707,  #Aidos Room
    977119532009291837,  #Valikhan Room
    1000999038784647228,  #Baurzhan Room
    1028904893144125500,  #обучение
    1203652885028802600,  #Ali-Nurasyl
    1095638837125988392,  #Dias Room
    996669365527269386,  #Владимир Room
    1158370586989441115,  #gosagro
    1173231115075592323,  #Аналитика
    1406969449214644346, # Нуржан
    1406969524330303538, # Sanzar
    1406969575488094329, # ADil
    1406969301864550430, #Nazgul
    1406969180447707247, # Gulnaz
    1437671685657464894,
    1460589657132761148,
]

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
user_original_channels = {}

@client.event
async def on_ready():
    print(f"[+] Бот вошёл как {client.user}")
    await wait_until_11_almaty()
    await do_daily_task()
    print("[~] Ожидание команды !shutdown...")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower() == "!shutdown":
        await message.channel.send("📦 Возвращаю пользователей на места и отключаюсь...")
        await return_users()
        await message.channel.send("✅ Все возвращены. Бот отключается.")
        await client.close()

    elif message.content.lower() == "!force_shutdown":
        await message.channel.send("⚠️ Принудительное выключение без возврата пользователей...")
        await client.close()

    elif message.content.lower() == "!run_now":
        await message.channel.send("⏱ Выполняю задачу прямо сейчас...")
        await do_daily_task()
        await message.channel.send("✅ Задача выполнена.")
        
    elif message.content.lower() == "!status":
        await message.channel.send("✅ Бот онлайн! Все системы работают.")


async def wait_until_11_almaty():
    tz = pytz.timezone("Asia/Almaty")
    now = datetime.datetime.now(tz)

    target_time = now.replace(hour=9, minute=1, second=0, microsecond=0)
    if now >= target_time:
        print("[~] Уже после 11:00 — начинаем сразу.")
        return

    wait_seconds = (target_time - now).total_seconds()
    print(f"[~] Ждём до 11:00 по Алматы ({wait_seconds:.0f} секунд)...")
    await asyncio.sleep(wait_seconds)

async def do_daily_task():
    tz = pytz.timezone('Asia/Almaty')
    now = datetime.datetime.now(tz)
    print(f"[~] Выполнение задачи в {now.strftime('%Y-%m-%d %H:%M')} по Алматы")
    
    guild = client.get_guild(TARGET_GUILD_ID)
    if not guild:
        print(f"[!] Бот не видит гильдию: {TARGET_GUILD_ID}")
        return
        
    target_channel = guild.get_channel(TARGET_VC_ID)
    text_channel = guild.get_channel(TARGET_TEXT_CHANNEL_ID)

    if not target_channel:
        print(f"[!] Голосовой канал не найден: {TARGET_VC_ID}")

    if text_channel:
        try:
            await text_channel.send("🌞 Доброе утро, коллеги! Желаю вам продуктивного дня! 💪")
            print(f"[✔] Сообщение отправлено в {text_channel.name}")
        except Exception as e:
            print(f"[✘] Не удалось отправить сообщение: {e}")

    for voice_channel in guild.voice_channels:
        if voice_channel.id not in SOURCE_VC_IDS:
            continue
        for member in voice_channel.members:
            if member.voice:
                try:
                    user_original_channels[member.id] = voice_channel.id
                    await member.move_to(target_channel)
                    print(f"[✔] Перемещён: {member.display_name} из {voice_channel.name}")
                except discord.Forbidden:
                    print(f"[✘] Нет прав: {member.display_name}")
                except Exception as e:
                    print(f"[✘] Ошибка при перемещении: {e}")

async def return_users():
    for guild in client.guilds:
        for member in guild.members:
            if member.id in user_original_channels and member.voice:
                original_channel_id = user_original_channels[member.id]
                original_channel = guild.get_channel(original_channel_id)
                if original_channel:
                    try:
                        await member.move_to(original_channel)
                        print(f"[⏪] {member.display_name} возвращён в {original_channel.name}")
                    except Exception as e:
                        print(f"[✘] Не удалось вернуть {member.display_name}: {e}")

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
