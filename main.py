import os
import pytz
import discord
import datetime
import asyncio

# Получаем токен из GitHub Secrets
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN не найден в переменных окружения!")

# Настройки каналов
TARGET_TEXT_CHANNEL_ID = 123456789012345678
TARGET_VC_ID = 1356206346491400282

SOURCE_VC_IDS = [
    1238369263006388245, 1082183176019005501, 1301517898484813896,
    943130959421767707, 977119532009291837, 1000999038784647228,
    1028904893144125500, 1203652885028802600, 1095638837125988392,
    996669365527269386, 1158370586989441115, 1173231115075592323,
    1406969449214644346, 1406969524330303538, 1406969575488094329,
    1406969301864550430, 1406969180447707247, 1437671685657464894
]

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
intents.guilds = True

client = discord.Client(intents=intents)
user_original_channels = {}

async def do_daily_task():
    # Проверяем день недели (0=Пн, 6=Вс)
    tz = pytz.timezone("Asia/Almaty")
    now = datetime.datetime.now(tz)
    if now.weekday() >= 5:
        print("[~] Выходные дни, задача не выполняется.")
        return

    print(f"[~] Выполнение задачи {now.strftime('%Y-%m-%d %H:%M')} по Алматы")

    for guild in client.guilds:
        target_channel = guild.get_channel(TARGET_VC_ID)
        text_channel = guild.get_channel(TARGET_TEXT_CHANNEL_ID)

        if text_channel:
            try:
                await text_channel.send("🌞 Доброе утро, коллеги! Желаю вам продуктивного дня! 💪")
                print(f"[✔] Сообщение отправлено в {text_channel.name}")
            except Exception as e:
                print(f"[✘] Не удалось отправить сообщение: {e}")

        if not target_channel:
            print(f"[!] Голосовой канал не найден: {TARGET_VC_ID}")
            continue

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

async def main():
    async with client:
        await client.login(TOKEN)
        await client.connect()
        await do_daily_task()
        await client.close()
        print("[~] Скрипт завершён.")

if __name__ == "__main__":
    asyncio.run(main())
