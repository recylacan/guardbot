import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

BOT_TOKEN = os.getenv("BOT_TOKEN")

FLOOD_LIMIT = 4
FLOOD_WINDOW = 4
timeout_duration = timedelta(days=7)
EXEMPT_CHANNEL_ID = 1499771195585724605
VOICE_CHANNEL_ID = 1499771195267088386

user_message_history = {}

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giris yapildi')
    print('Guard bot aktif')
    print('Flood limit: 4 mesaj / 4 saniye')
    
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel is not None:
            await voice_channel.connect()
            print(f'Ses kanalina baglanildi: {voice_channel.name}')
        else:
            print('Ses kanali bulunamadi')
    except Exception as e:
        print(f'Ses kanalina baglanilamadi: {e}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.channel.id == EXEMPT_CHANNEL_ID:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    current_time = datetime.now()

    if user_id not in user_message_history:
        user_message_history[user_id] = []

    user_message_history[user_id].append(current_time)

    user_message_history[user_id] = [
        t for t in user_message_history[user_id] 
        if current_time - t <= timedelta(seconds=FLOOD_WINDOW)
    ]

    if len(user_message_history[user_id]) > FLOOD_LIMIT:
        
        try:
            await message.author.timeout(timeout_duration, reason="Flood koruma ihlali - 7 gun timeout")
            print(f'{message.author.name} adli kullaniciya 7 gun timeout verildi')
        except discord.Forbidden:
            print('Yetki yok: timeout verilemedi')
        except Exception as e:
            print(f'Timeout hatasi: {e}')

        try:
            async for msg in message.channel.history(limit=200):
                if msg.author.id == user_id:
                    try:
                        await msg.delete()
                    except:
                        pass
            print(f'{message.author.name} adli kullanicinin mesajlari silindi')
        except Exception as e:
            print(f'Mesaj silme hatasi: {e}')

        try:
            dm_channel = await message.author.create_dm()
            
            embed = discord.Embed(
                title="**KORUMA SISTEMI**",
                description="**KULLANICI SUSTURULDU**",
                color=0xff0000
            )
            
            embed.add_field(
                name="**KULLANICI BILGILERI**",
                value=f"**Kullanici:** {message.author.mention}\n**Kullanici Adi:** {message.author.name}\n**ID:** {str(message.author.id)}",
                inline=False
            )
            
            embed.add_field(
                name="**CEZA BILGILERI**",
                value="**Ceza Nedeni:** FLOOD\n**Ceza Suresi:** 7 GUN TIMEOUT\n**Ceza Durumu:** AKTIF",
                inline=False
            )
            
            embed.add_field(
                name="**ACIKLAMA**",
                value="Belirlenen sure icerisinde izin verilenden fazla mesaj gonderdiginiz icin 7 gun boyunca sunucuda konusamazsiniz. Tum mesajlariniz sistemimiz tarafindan otomatik silinmistir.",
                inline=False
            )
            
            embed.set_footer(text="made by recyla | Flood Koruma Sistemi")
            
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            await dm_channel.send(embed=embed)
            print(f'DM mesaji {message.author.name} adli kullaniciya gonderildi')
        except Exception as e:
            print(f'DM gonderilemedi: {e}')

        try:
            if user_id in user_message_history:
                del user_message_history[user_id]
        except:
            pass

        return

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    
    if voice_client is None:
        try:
            voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
            if voice_channel is not None:
                await voice_channel.connect()
                print('Ses kanalina yeniden baglanildi')
        except:
            pass
        return

bot.run(BOT_TOKEN)
