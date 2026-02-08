import discord
from discord import app_commands
import requests
import json
import time
from datetime import datetime, timedelta
import asyncio
import os

# ===== CONFIG =====
BOT_TOKEN = os.getenv("BOT_TOKEN", "MTQ2OTk1NTkyNDk2OTEyNzk4Nw.GO2WqO.hJqUw19uraQ4FK1KQyF7luarFq_l9Zk4fe60Xk")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://discord.com/api/webhooks/1469957908971262015/nFFEmb9YRziFzFyAYap5KoQLUglFGB4QXKKenqihglN5vrvl2AhqsQ6kY3Ar2T-9o5cc")

# Gist ID akan dibuat otomatis saat pertama kali run
GIST_ID = os.getenv("GIST_ID", None)
GIST_FILENAME = "vip_database.json"

# ===== GITHUB GIST FUNCTIONS =====
def create_gist():
    """Buat Gist baru untuk VIP database"""
    url = "https://api.github.com/gists"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "description": "Vortex VIP Database",
        "public": False,
        "files": {
            GIST_FILENAME: {
                "content": json.dumps({}, indent=2)
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        gist_data = response.json()
        gist_id = gist_data["id"]
        print(f"✅ Gist created! ID: {gist_id}")
        print(f"📋 RAW URL: https://gist.githubusercontent.com/raw/{gist_id}/{GIST_FILENAME}")
        
        # Save to file
        with open("gist_id.txt", "w") as f:
            f.write(gist_id)
        
        return gist_id
    else:
        print(f"❌ Failed to create Gist: {response.text}")
        return None

def get_vip_data():
    """Download VIP data dari Gist"""
    global GIST_ID
    
    if not GIST_ID:
        return {}
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            gist_data = response.json()
            content = gist_data["files"][GIST_FILENAME]["content"]
            return json.loads(content)
        return {}
    except Exception as e:
        print(f"❌ Error getting VIP data: {e}")
        return {}

def update_vip_data(data):
    """Update VIP data ke Gist"""
    global GIST_ID
    
    if not GIST_ID:
        print("❌ Gist ID not set!")
        return False
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        payload = {
            "files": {
                GIST_FILENAME: {
                    "content": json.dumps(data, indent=2)
                }
            }
        }
        
        response = requests.patch(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            print(f"✅ VIP data updated!")
            return True
        else:
            print(f"❌ Failed to update Gist: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating Gist: {e}")
        return False

def send_webhook(message, color=0x5865F2):
    """Kirim notifikasi ke Discord webhook"""
    try:
        embed = {
            "title": "🔔 Vortex VIP System",
            "description": message,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Vortex's Bot"}
        }
        
        data = {"embeds": [embed]}
        requests.post(WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"❌ Webhook error: {e}")

# ===== DISCORD BOT =====
intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    global GIST_ID
    
    # Load Gist ID from file if exists
    try:
        with open("gist_id.txt", "r") as f:
            saved_id = f.read().strip()
            if saved_id:
                GIST_ID = saved_id
                print(f"📂 Loaded Gist ID: {GIST_ID}")
    except:
        pass
    
    # Create Gist if not exists
    if not GIST_ID:
        print("🔄 Creating new Gist...")
        GIST_ID = create_gist()
        
        if GIST_ID:
            print(f"\n{'='*60}")
            print("✅ GIST BERHASIL DIBUAT!")
            print(f"{'='*60}")
            print(f"📋 GIST ID: {GIST_ID}")
            print(f"🔗 RAW URL: https://gist.githubusercontent.com/raw/{GIST_ID}/{GIST_FILENAME}")
            print(f"\n⚠️  PENTING! COPY URL INI KE SCRIPT ROBLOX:")
            print(f"    local GIST_URL = \"https://gist.githubusercontent.com/raw/{GIST_ID}/{GIST_FILENAME}\"")
            print(f"{'='*60}\n")
    
    await tree.sync()
    print(f"✅ Vortex's Bot online sebagai {bot.user}")
    print(f"📊 Connected to {len(bot.guilds)} server(s)")
    send_webhook("✅ Vortex's Bot is now online!", 0x00FF00)

# ===== COMMAND: /addvip =====
@tree.command(name="addvip", description="Add VIP user")
@app_commands.describe(
    username="Roblox username",
    days="Durasi VIP dalam hari"
)
async def addvip(interaction: discord.Interaction, username: str, days: int):
    await interaction.response.defer()
    
    if days <= 0:
        await interaction.followup.send("❌ Durasi harus lebih dari 0 hari!")
        return
    
    vip_data = get_vip_data()
    expiry_time = int(time.time()) + (days * 86400)
    
    vip_data[username] = {
        "expiry": expiry_time,
        "added": int(time.time()),
        "days": days,
        "added_by": str(interaction.user)
    }
    
    if update_vip_data(vip_data):
        expiry_date = datetime.fromtimestamp(expiry_time).strftime("%Y-%m-%d %H:%M:%S")
        
        embed = discord.Embed(
            title="✅ VIP Added Successfully",
            color=0x00FF00
        )
        embed.add_field(name="Username", value=username, inline=True)
        embed.add_field(name="Duration", value=f"{days} days", inline=True)
        embed.add_field(name="Expires", value=expiry_date, inline=False)
        embed.set_footer(text=f"Added by {interaction.user}")
        
        await interaction.followup.send(embed=embed)
        
        send_webhook(
            f"✅ **VIP Added**\n"
            f"👤 Username: `{username}`\n"
            f"⏱️ Duration: `{days} days`\n"
            f"📅 Expires: `{expiry_date}`\n"
            f"👮 By: `{interaction.user}`",
            0x00FF00
        )
    else:
        await interaction.followup.send("❌ Gagal update database!")

# ===== COMMAND: /removevip =====
@tree.command(name="removevip", description="Remove VIP user")
@app_commands.describe(username="Roblox username")
async def removevip(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    
    vip_data = get_vip_data()
    
    if username in vip_data:
        del vip_data[username]
        
        if update_vip_data(vip_data):
            embed = discord.Embed(
                title="✅ VIP Removed",
                description=f"User `{username}` telah dihapus dari VIP",
                color=0xFF0000
            )
            embed.set_footer(text=f"Removed by {interaction.user}")
            
            await interaction.followup.send(embed=embed)
            
            send_webhook(
                f"🗑️ **VIP Removed**\n"
                f"👤 Username: `{username}`\n"
                f"👮 By: `{interaction.user}`",
                0xFF0000
            )
        else:
            await interaction.followup.send("❌ Gagal update database!")
    else:
        await interaction.followup.send(f"❌ User `{username}` tidak ditemukan!")

# ===== COMMAND: /checkvip =====
@tree.command(name="checkvip", description="Check VIP status")
@app_commands.describe(username="Roblox username")
async def checkvip(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    
    vip_data = get_vip_data()
    
    if username in vip_data:
        data = vip_data[username]
        current_time = int(time.time())
        days_left = (data['expiry'] - current_time) // 86400
        
        if data['expiry'] > current_time:
            expiry_date = datetime.fromtimestamp(data['expiry']).strftime("%Y-%m-%d %H:%M:%S")
            
            embed = discord.Embed(
                title="✅ VIP Active",
                color=0x00FF00
            )
            embed.add_field(name="Username", value=username, inline=True)
            embed.add_field(name="Days Left", value=f"{days_left} days", inline=True)
            embed.add_field(name="Expires", value=expiry_date, inline=False)
            
            await interaction.followup.send(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ VIP Expired",
                description=f"VIP untuk `{username}` sudah expired!",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send(f"❌ `{username}` tidak ada di VIP list!")

# ===== COMMAND: /listvip =====
@tree.command(name="listvip", description="List all VIP users")
async def listvip(interaction: discord.Interaction):
    await interaction.response.defer()
    
    vip_data = get_vip_data()
    
    if not vip_data:
        await interaction.followup.send("📭 Tidak ada VIP user.")
        return
    
    current_time = int(time.time())
    active_vips = []
    expired_vips = []
    
    for username, data in vip_data.items():
        days_left = (data['expiry'] - current_time) // 86400
        
        if data['expiry'] > current_time:
            active_vips.append(f"✅ `{username}` - {days_left} days left")
        else:
            expired_vips.append(f"❌ `{username}` - EXPIRED")
    
    embed = discord.Embed(
        title="📋 VIP Users List",
        color=0x5865F2
    )
    
    if active_vips:
        embed.add_field(
            name=f"Active VIPs ({len(active_vips)})",
            value="\n".join(active_vips),
            inline=False
        )
    
    if expired_vips:
        embed.add_field(
            name=f"Expired VIPs ({len(expired_vips)})",
            value="\n".join(expired_vips),
            inline=False
        )
    
    embed.set_footer(text=f"Total: {len(vip_data)} users")
    
    await interaction.followup.send(embed=embed)

# ===== COMMAND: /cleanexpired =====
@tree.command(name="cleanexpired", description="Hapus semua VIP yang expired")
async def cleanexpired(interaction: discord.Interaction):
    await interaction.response.defer()
    
    vip_data = get_vip_data()
    current_time = int(time.time())
    
    expired_users = [user for user, data in vip_data.items() if data['expiry'] <= current_time]
    
    if not expired_users:
        await interaction.followup.send("✅ Tidak ada VIP expired!")
        return
    
    for user in expired_users:
        del vip_data[user]
    
    if update_vip_data(vip_data):
        embed = discord.Embed(
            title="🗑️ Expired VIPs Cleaned",
            description=f"Berhasil menghapus {len(expired_users)} expired VIP",
            color=0xFF0000
        )
        embed.add_field(
            name="Deleted Users",
            value="\n".join([f"• {user}" for user in expired_users]),
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
        send_webhook(
            f"🗑️ **Cleaned Expired VIPs**\n"
            f"Deleted: {len(expired_users)} users",
            0xFF0000
        )
    else:
        await interaction.followup.send("❌ Gagal update database!")

# ===== COMMAND: /gisturl =====
@tree.command(name="gisturl", description="Get Gist URL for Roblox script")
async def gisturl(interaction: discord.Interaction):
    await interaction.response.defer()
    
    if GIST_ID:
        raw_url = f"https://gist.githubusercontent.com/raw/{GIST_ID}/{GIST_FILENAME}"
        
        embed = discord.Embed(
            title="📋 Gist URL",
            description=f"Copy URL ini ke script Roblox:",
            color=0x00FF00
        )
        embed.add_field(
            name="RAW URL",
            value=f"```{raw_url}```",
            inline=False
        )
        embed.add_field(
            name="Script Roblox",
            value=f"```lua\nlocal GIST_URL = \"{raw_url}\"\n```",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
    else:
        await interaction.followup.send("❌ Gist belum dibuat!")

# ===== AUTO CHECK EXPIRED =====
async def auto_check_expired():
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        try:
            vip_data = get_vip_data()
            current_time = int(time.time())
            
            newly_expired = []
            
            for username, data in list(vip_data.items()):
                if current_time > data['expiry'] and current_time - data['expiry'] < 86400:
                    newly_expired.append(username)
            
            if newly_expired:
                send_webhook(
                    f"⏰ **VIP Expired Alert**\n" +
                    "\n".join([f"• `{user}`" for user in newly_expired]),
                    0xFFAA00
                )
        except Exception as e:
            print(f"❌ Auto check error: {e}")
        
        await asyncio.sleep(21600)  # 6 hours

# ===== RUN BOT =====
if __name__ == "__main__":
    bot.loop.create_task(auto_check_expired())
    bot.run(BOT_TOKEN)
