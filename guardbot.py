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

# TAG/ETİKET ROLÜ VE MESAJ KANALI
HEDEF_ROLE_ID = 1499771194323243279     # Etiket Rol ID
KANAL_ID = 1499771195585724598          # Mesaj Kanal ID

# DURUM ROLÜ AYARI (Aynı ID kullanılıyor)
DURUM_ROLE_ID = 1499771194323243279     # Durumda verilecek rol ID
DURUM_TEXT = "/anonymousdc"             # Durumda aranacak yazı

# --- BOT BAŞLANGIÇ ---
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Kullanıcı mesaj geçmişi (flood kontrolü için)
user_message_history = {}

# Rol alan kullanıcıları takip et (2 kere mesaj atmasın diye)
role_given_users = set()
role_removed_users = set()

# --- BOT HAZIR ---
@bot.event
async def on_ready():
    print(f'Bot {bot.user} olarak giriş yapıldı')
    print('Guard bot aktif')
    print('Flood limit: 1 saniyede 3 mesaj (7 gün timeout)')
    print('Tag sistemi aktif (Rol alınca mesaj)')
    print('Durum sistemi aktif (/anonymousdc = rol)')
    
    try:
        voice_channel = bot.get_channel(VOICE_CHANNEL_ID)
        if voice_channel is not None:
            await voice_channel.connect()
            print(f'Ses kanalına bağlanıldı: {voice_channel.name}')
        else:
            print('Ses kanalı bulunamadı')
    except Exception as e:
        print(f'Ses kanalına bağlanılamadı: {e}')

# --- 1. FLOOD KORUMA SİSTEMİ ---
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
            await message.author.timeout(timeout_duration, reason="Flood koruma ihlali - 7 gün timeout")
            print(f'{message.author.name} adlı kullanıcıya 7 GÜN timeout verildi')
        except discord.Forbidden:
            print('Yetki yok: timeout verilemedi')
        except Exception as e:
            print(f'Timeout hatası: {e}')

        try:
            async for msg in message.channel.history(limit=50):
                if msg.author.id == user_id:
                    try:
                        await msg.delete()
                    except:
                        pass
            print('Kullanıcının mesajları silindi')
        except Exception as e:
            print(f'Mesaj silme hatası: {e}')

        try:
            dm_channel = await message.author.create_dm()
            
            embed = discord.Embed(
                title="KORUMA SISTEMI",
                description="SUSTURULDUNUZ",
                color=0xff0000
            )
            
            embed.add_field(
                name="KULLANICI BILGILERI",
                value=f"```\nKullanici     : {message.author.name}\nID            : {str(message.author.id)}\n```",
                inline=False
            )
            
            embed.add_field(
                name="CEZA BILGILERI",
                value=f"```\nCeza Nedeni   : FLOOD (1 saniyede {len(user_message_history[user_id])} mesaj)\nCeza Suresi   : 7 GÜN TIMEOUT\nCeza Durumu   : AKTIF\n```",
                inline=False
            )
            
            embed.add_field(
                name="ACIKLAMA",
                value="```\n1 saniye içinde çok fazla mesaj gönderdiğiniz için\n7 gün boyunca sunucuda konuşamazsınız.\nTüm mesajlarınız silinmiştir.\n```",
                inline=False
            )
            
            embed.add_field(
                name="",
                value="made by Recyla | Koruma Sistemi",
                inline=False
            )
            
            if message.author.avatar:
                embed.set_thumbnail(url=message.author.avatar.url)
            
            await dm_channel.send(embed=embed)
        except:
            pass

        if user_id in user_message_history:
            del user_message_history[user_id]
        
        return

    await bot.process_commands(message)

# --- 2. ROL ALINCA MESAJ ATMA ---
@bot.event
async def on_member_update(before, after):
    # ROL EKLENDİĞİNDE
    if HEDEF_ROLE_ID not in [r.id for r in before.roles] and HEDEF_ROLE_ID in [r.id for r in after.roles]:
        if after.id not in role_given_users:
            role_given_users.add(after.id)
            
            kanal = bot.get_channel(KANAL_ID)
            if kanal:
                embed = discord.Embed(
                    title="KRALLIĞA HOŞGELDİN",
                    description=f"**{after.mention} Krallığa Hoşgeldin Dostum!**",
                    color=0x2b2d31
                )
                
                embed.add_field(
                    name="",
                    value="Sunucumuzun etiketini (tag'ini) aldığın için teşekkürler! Artık topluluğumuzu temsil ediyorsun. Bu etiketi taşıdığın sürece bu özel role sahip olacaksın.",
                    inline=False
                )
                
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                
                await kanal.send(embed=embed)
                print(f'{after.name} adlı kullanıcı tag aldı, hoşgeldin mesajı atıldı.')
    
    # ROL KALDIRILDIĞINDA (Tag kaldırılınca)
    elif HEDEF_ROLE_ID in [r.id for r in before.roles] and HEDEF_ROLE_ID not in [r.id for r in after.roles]:
        if after.id not in role_removed_users:
            role_removed_users.add(after.id)
            
            rol = after.guild.get_role(HEDEF_ROLE_ID)
            if rol:
                try:
                    await after.remove_roles(rol)
                    print(f'{after.name} adlı kullanıcıdan {rol.name} rolü çekildi (Tag kaldırıldı)')
                    
                    kanal = bot.get_channel(KANAL_ID)
                    if kanal:
                        embed = discord.Embed(
                            title="ROL KALDIRILDI",
                            description=f"**{after.mention} adlı kullanıcıdan etiket rolü kaldırıldı!**",
                            color=0xff0000
                        )
                        embed.add_field(
                            name="",
                            value="Üzgünüz, artık topluluğumuzu temsil etmiyorsun. Eğer tekrar katılmak istersen etiketini tekrar alabilirsin.",
                            inline=False
                        )
                        embed.set_thumbnail(url=after.display_avatar.url)
                        embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                        await kanal.send(embed=embed)
                        print(f'{after.name} adlı kullanıcıdan rol çekildi, uyarı mesajı atıldı.')
                except Exception as e:
                    print(f'Rol çekme hatası: {e}')

# --- 3. DURUM GÜNCELLENİNCE OTO ROL (DÜZELTİLDİ) ---
@bot.event
async def on_presence_update(before, after):
    # SADECE DURUM METNİ DEĞİŞTİĞİNDE ÇALIŞSIN
    # Eğer before.activity ve after.activity aynıysa (sadece aktiflik değiştiyse) işlem yapma
    before_text = before.activity.name if before.activity else ""
    after_text = after.activity.name if after.activity else ""
    
    # Eğer durum metni değişmediyse (sadece online/offline olduysa) çık
    if before_text == after_text:
        return
    
    rol = after.guild.get_role(DURUM_ROLE_ID)
    
    # Durumda /anonymousdc VARSA ve kullanıcıda rol YOKSA → rol ver
    if DURUM_TEXT.lower() in after_text.lower() and rol and rol not in after.roles:
        if after.id not in role_given_users:
            role_given_users.add(after.id)
            
            try:
                await after.add_roles(rol)
                print(f'{after.name} adlı kullanıcıya {rol.name} rolü verildi (Durum: {after_text})')
                
                kanal = bot.get_channel(KANAL_ID)
                if kanal:
                    embed = discord.Embed(
                        title="KRALLIĞA HOŞGELDİN",
                        description=f"**{after.mention} Krallığa Hoşgeldin Dostum!**",
                        color=0x2b2d31
                    )
                    embed.add_field(
                        name="",
                        value="Durumuna /anonymousdc yazarak topluluğumuza katıldın! Artık bu özel role sahipsin.",
                        inline=False
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                    await kanal.send(embed=embed)
                    print(f'{after.name} durumdan rol aldı, hoşgeldin mesajı atıldı.')
            except discord.Forbidden:
                print('Yetki hatası! Botun rolü, verilecek rolden yukarıda olmalı.')
            except Exception as e:
                print(f'Hata: {e}')
    
    # Durumda /anonymousdc YOKSA ve kullanıcıda rol VARSA → rol çek
    elif DURUM_TEXT.lower() not in after_text.lower() and rol and rol in after.roles:
        if after.id not in role_removed_users:
            role_removed_users.add(after.id)
            
            try:
                await after.remove_roles(rol)
                print(f'{after.name} adlı kullanıcıdan {rol.name} rolü çekildi (Durum kaldırıldı: {after_text})')
                
                kanal = bot.get_channel(KANAL_ID)
                if kanal:
                    embed = discord.Embed(
                        title="ROL KALDIRILDI",
                        description=f"**{after.mention} adlı kullanıcıdan durum rolü kaldırıldı!**",
                        color=0xff0000
                    )
                    embed.add_field(
                        name="",
                        value="Durumundan /anonymousdc yazısını kaldırdığın için rolün alındı. Tekrar almak için durumuna /anonymousdc yazabilirsin.",
                        inline=False
                    )
                    embed.set_thumbnail(url=after.display_avatar.url)
                    embed.set_author(name=after.name, icon_url=after.display_avatar.url)
                    await kanal.send(embed=embed)
                    print(f'{after.name} adlı kullanıcıdan rol çekildi, uyarı mesajı atıldı.')
            except Exception as e:
                print(f'Rol çekme hatası: {e}')

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
        print("BOT_TOKEN bulunamadı! Lütfen .env dosyanızı kontrol edin.")
