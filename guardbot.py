import discord
from discord.ext import commands
import asyncio
import os
from datetime import datetime, timedelta
from collections import deque

# --- AYARLAR ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# FLOOD KORUMA AYARLARI
FLOOD_LIMIT = 3           # 1 saniyede 3 mesaj limit (3 ve üzeri 7 gün timeout)
FLOOD_WINDOW = 1          # 1 saniye zaman aralığı
timeout_duration = timedelta(days=7)

# KORUMA DIŞI KANAL (Bu kanalda flood koruma çalışmaz)
EXEMPT_CHANNEL_ID = 1499771195585724605

# SES KANALI
VOICE_CHANNEL_ID = 1499771195267088386

# TAG/ETİKET ROLÜ VE MESAJ KANALI
HEDEF_ROLE_ID = 1499771194323243279     # Etiket Rol ID
KANAL_ID = 1499771195585724598          # Mesaj Kanal ID (Tag alınca mesaj atılacak)

# DURUM ROLÜ AYARI (Aynı ID kullanılıyor)
DURUM_ROLE_ID = 1499771194323243279     # Durumda verilecek rol ID
DURUM_TEXT = "/anonymousdc"             # Durumda aranacak yazı

# --- BOT BAŞLANGIÇ ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Kullanıcı mesaj geçmişi (flood kontrolü için)
user_message_history = {}

# --- BOT HAZIR ---
@bot.event
async def on_ready():
    print(f'🤖 {bot.user} olarak giriş yapıldı')
    print('🛡️ Guard bot aktif')
    print('⚡ Flood limit: 1 saniyede 3 mesaj (7 gün timeout)')
    print('🏷️ Tag sistemi aktif (Rol alınca mesaj)')
    print('📢 Durum sistemi aktif (/anonymousdc = rol)')
    
    # Ses kanalına bağlan
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel is not None:
            await voice_channel.connect()
            print(f'🔊 Ses kanalına bağlanıldı: {voice_channel.name}')
        else:
            print('⚠️ Ses kanalı bulunamadı')
    except Exception as e:
        print(f'❌ Ses kanalına bağlanılamadı: {e}')

# --- 1. FLOOD KORUMA SİSTEMİ ---
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Muaf kanal kontrolü
    if message.channel.id == EXEMPT_CHANNEL_ID:
        await bot.process_commands(message)
        return

    user_id = message.author.id
    current_time = datetime.now()

    # Kullanıcı geçmişini güncelle
    if user_id not in user_message_history:
        user_message_history[user_id] = []

    user_message_history[user_id].append(current_time)

    # 1 saniye içindeki mesajları temizle
    user_message_history[user_id] = [
        t for t in user_message_history[user_id] 
        if (current_time - t).total_seconds() <= FLOOD_WINDOW
    ]

    # 1 saniyede 3 veya daha fazla mesaj = 7 gün timeout
    if len(user_message_history[user_id]) >= 3:
        
        # Kullanıcıya timeout at
        try:
            # 7 GÜN TIMEOUT
            await message.author.timeout(timeout_duration, reason="Flood koruma ihlali - 7 gün timeout")
            print(f'⛔ {message.author.name} ({message.author.id}) adlı kullanıcıya 7 GÜN timeout verildi (1 saniyede {len(user_message_history[user_id])} mesaj)')
        except discord.Forbidden:
            print('❌ Yetki yok: timeout verilemedi')
        except Exception as e:
            print(f'❌ Timeout hatası: {e}')

        # Kullanıcının son 50 mesajını sil
        silinen = 0
        try:
            async for msg in message.channel.history(limit=50):
                if msg.author.id == user_id:
                    try:
                        await msg.delete()
                        silinen += 1
                    except:
                        pass
            print(f'🗑️ {silinen} mesaj silindi (Kullanıcı: {message.author.name})')
        except Exception as e:
            print(f'❌ Mesaj silme hatası: {e}')

        # DM bilgilendirmesi gönder
        try:
            dm_channel = await message.author.create_dm()
            
            embed = discord.Embed(
                title="🛡️ KORUMA SISTEMI",
                description="⛔ **SUSTURULDUNUZ**",
                color=0xff0000
            )
            
            embed.add_field(
                name="👤 KULLANICI BILGILERI",
                value=f"```\nKullanici     : {message.author.name}\nID            : {str(message.author.id)}\n```",
                inline=False
            )
            
            embed.add_field(
                name="⚖️ CEZA BILGILERI",
                value=f"```\nCeza Nedeni   : FLOOD (1 saniyede {len(user_message_history[user_id])} mesaj)\nCeza Suresi   : 7 GÜN TIMEOUT\nCeza Durumu   : AKTIF\n```",
                inline=False
            )
            
            embed.add_field(
                name="📝 ACIKLAMA",
                value="```\n1 saniye içinde çok fazla mesaj gönderdiğiniz için\n7 gün boyunca sunucuda konuşamazsınız.\nTüm mesajlarınız silinmiştir.\n```",
                inline=False
            )
            
            embed.add_field(
                name="",
                value="**made by Recyla | Koruma Sistemi**",
                inline=False
            )
            
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            await dm_channel.send(embed=embed)
        except:
            pass

        # Kullanıcı geçmişini temizle
        if user_id in user_message_history:
            del user_message_history[user_id]
        
        return

    await bot.process_commands(message)

# --- 2. ROL ALINCA MESAJ ATMA (TAG SİSTEMİ) ---
@bot.event
async def on_member_update(before, after):
    # Hedef rol eklenmiş mi kontrol et
    if HEDEF_ROLE_ID not in [r.id for r in before.roles] and HEDEF_ROLE_ID in [r.id for r in after.roles]:
        
        kanal = bot.get_channel(KANAL_ID)
        if kanal:
            embed = discord.Embed(
                title="Hoşgeldin !",
                description="**Krallığa Hoşgeldin Dostum**",
                color=0xFF0000
            )
            # Görseldeki elmas ikonu
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/902106431051948092.png")
            
            await kanal.send(embed=embed)
            print(f'📨 {after.name} adlı kullanıcı tag aldı, hoşgeldin mesajı atıldı.')

# --- 3. DURUM GÜNCELLENİNCE OTO ROL ---
@bot.event
async def on_presence_update(before, after):
    # Kullanıcının durumu varsa kontrol et
    if after.activity:
        # Durum metnini küçük harfe çevirip kontrol et
        if DURUM_TEXT.lower() in after.activity.name.lower():
            
            # Rolü al
            rol = after.guild.get_role(DURUM_ROLE_ID)
            if rol:
                # Eğer kullanıcıda bu rol yoksa ver
                if rol not in after.roles:
                    try:
                        await after.add_roles(rol)
                        print(f'✅ {after.name} adlı kullanıcıya {rol.name} rolü verildi (Durum: {after.activity.name})')
                    except discord.Forbidden:
                        print('❌ Yetki hatası! Botun rolü, verilecek rolden yukarıda olmalı.')
                    except Exception as e:
                        print(f'❌ Hata: {e}')
            else:
                print(f'⚠️ Rol bulunamadı! ID: {DURUM_ROLE_ID}')

# --- 4. SES KANALI KONTROLÜ ---
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
        return

# --- BOTU BAŞLAT ---
if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("❌ BOT_TOKEN bulunamadı! Lütfen .env dosyanızı kontrol edin.")
