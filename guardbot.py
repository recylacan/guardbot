import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime, timedelta
from collections import deque

# --- AYARLAR ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# FLOOD KORUMA AYARLARI
FLOOD_LIMIT = 3
FLOOD_WINDOW = 1
timeout_duration = timedelta(days=7)

# KORUMA DIŞI KANAL
EXEMPT_CHANNEL_ID = 1499771195585724605

# SES KANALI
VOICE_CHANNEL_ID = 1499771195267088386

# ETİKET ROLÜ ADI (ANON)
TARGET_ROLE_NAME = "ANON"  # <-- Rolün tam adı (Büyük harf önemli değil)

# MESAJ KANALI
KANAL_ID = 1499771195585724598

# DURUM ROLÜ AYARI (Aynı rol)
DURUM_ROLE_ID = 1499771194323243279
DURUM_TEXT = "/anonymousdc"

# RESİM URL
THUMBNAIL_URL = "https://i.ibb.co/hJFwL8Yb/indir-4.jpg"

# --- BOT BAŞLANGIÇ ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

user_message_history = {}
role_given_users = set()

# --- BOT HAZIR ---
@bot.event
async def on_ready():
    print(f'🤖 {bot.user} olarak giriş yapıldı')
    print('🛡️ Guard bot aktif')
    print(f'🏷️ Hedef Rol: {TARGET_ROLE_NAME}')
    print('📢 Durum sistemi aktif (/anonymousdc = rol)')
    
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel is not None:
            await voice_channel.connect()
            print(f'🔊 Ses kanalına bağlanıldı: {voice_channel.name}')
    except Exception as e:
        print(f'❌ Ses kanalına bağlanılamadı: {e}')

# --- FLOOD KORUMA ---
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
        if (current_time - t).total_seconds() <= FLOOD_WINDOW
    ]

    if len(user_message_history[user_id]) >= 3:
        try:
            await message.author.timeout(timeout_duration, reason="Flood koruma - 7 gün timeout")
            print(f'⛔ {message.author.name} timeout verildi')
        except:
            pass

        try:
            async for msg in message.channel.history(limit=50):
                if msg.author.id == user_id:
                    try:
                        await msg.delete()
                    except:
                        pass
        except:
            pass

        if user_id in user_message_history:
            del user_message_history[user_id]
        
        return

    await bot.process_commands(message)

# --- 2. ROL ALINCA MESAJ ATMA (ANON ROLÜ) ---
@bot.event
async def on_member_update(before, after):
    # ROL EKLENDİ Mİ KONTROL ET (ANON ROLÜ)
    role_added = False
    role_removed = False
    
    # Hangi rollerin eklendiğini/çıkarıldığını bul
    added_roles = [r for r in after.roles if r not in before.roles]
    removed_roles = [r for r in before.roles if r not in after.roles]
    
    # ANON rolü eklendiyse
    for role in added_roles:
        if role.name.upper() == TARGET_ROLE_NAME.upper():  # Büyük/küçük harf duyarlı olmasın
            role_added = True
            break
    
    # ANON rolü kaldırıldıysa
    for role in removed_roles:
        if role.name.upper() == TARGET_ROLE_NAME.upper():
            role_removed = True
            break
    
    # --- ROL EKLENDİĞİNDE ---
    if role_added:
        if after.id not in role_given_users:
            role_given_users.add(after.id)
            
            kanal = bot.get_channel(KANAL_ID)
            if kanal:
                embed = discord.Embed(
                    title=" KRALLIĞA HOŞGELDİN CANO ",
                    description=f"**{after.mention} Krallığa Hoşgeldin Dostum!**",
                    color=0x2b2d31
                )
                embed.add_field(
                    name="",
                    value="**ANON** etiketini aldığın için teşekkürler! Artık topluluğumuzu temsil ediyorsun.",
                    inline=False
                )
                embed.set_thumbnail(url=THUMBNAIL_URL)
                embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                await kanal.send(embed=embed)
                print(f'📨 {after.name} adlı kullanıcı ANON rolü aldı!')

    # --- ROL KALDIRILDIĞINDA ---
    elif role_removed:
        kanal = bot.get_channel(KANAL_ID)
        if kanal:
            embed = discord.Embed(
                title="⚠️ ROL KALDIRILDI",
                description=f"**{after.mention} adlı kullanıcıdan ANON rolü kaldırıldı!**",
                color=0xff0000
            )
            embed.add_field(
                name="",
                value="Artık topluluğumuzu temsil etmiyorsun. Tekrar katılmak istersen ANON etiketini tekrar alabilirsin.",
                inline=False
            )
            embed.set_thumbnail(url=THUMBNAIL_URL)
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
            await kanal.send(embed=embed)
            print(f'📨 {after.name} adlı kullanıcıdan ANON rolü kaldırıldı!')

# --- 3. DURUM GÜNCELLENİNCE OTO ROL ---
@bot.event
async def on_presence_update(before, after):
    if after.activity:
        if DURUM_TEXT.lower() in after.activity.name.lower():
            rol = after.guild.get_role(DURUM_ROLE_ID)
            if rol and rol not in after.roles:
                try:
                    await after.add_roles(rol)
                    print(f'✅ {after.name} durumdan rol aldı')
                    
                    if after.id not in role_given_users:
                        role_given_users.add(after.id)
                        kanal = bot.get_channel(KANAL_ID)
                        if kanal:
                            embed = discord.Embed(
                                title="✨ KRALLIĞA HOŞGELDİN ✨",
                                description=f"**{after.mention} Krallığa Hoşgeldin Dostum!**",
                                color=0x2b2d31
                            )
                            embed.add_field(
                                name="",
                                value="Durumuna **/anonymousdc** yazarak topluluğumuza katıldın! Artık bu özel role sahipsin.",
                                inline=False
                            )
                            embed.set_thumbnail(url=THUMBNAIL_URL)
                            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                            await kanal.send(embed=embed)
                except:
                    pass
        else:
            rol = after.guild.get_role(DURUM_ROLE_ID)
            if rol and rol in after.roles:
                try:
                    await after.remove_roles(rol)
                    print(f'❌ {after.name} durumdan rol çekildi')
                    kanal = bot.get_channel(KANAL_ID)
                    if kanal:
                        embed = discord.Embed(
                            title=" ROL KALDIRILDI ",
                            description=f"**{after.mention} adlı kullanıcıdan durum rolü kaldırıldı!**",
                            color=0xff0000
                        )
                        embed.add_field(
                            name="",
                            value="Durumundan /anonymousdc yazısını kaldırdığın için rolün alındı.",
                            inline=False
                        )
                        embed.set_thumbnail(url=THUMBNAIL_URL)
                        embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                        await kanal.send(embed=embed)
                except:
                    pass

# --- SES KANALI ---
@bot.event
async def on_voice_state_update(member, before, after):
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if voice_client is None:
        try:
            voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
            if voice_channel is not None:
                await voice_channel.connect()
        except:
            pass

# --- BOTU BAŞLAT ---
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("❌ BOT_TOKEN bulunamadı!")
