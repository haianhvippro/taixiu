import discord
from discord.ext import commands
import asyncio
import json
import os
import random
from flask import Flask
from threading import Thread

# ----- CONFIG -----
TOKEN = os.getenv("TOKEN")  # Token được lấy từ biến môi trường
DATA_FILE = "balances.json"
CHANNEL_FILE = "channel.json"

# ----- FLASK UPTIME -----
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot đang chạy!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

# ----- LOAD & SAVE -----
def load_json(filename, default):
    if not os.path.exists(filename):
        return default
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

balances = load_json(DATA_FILE, {})
allowed_channel = load_json(CHANNEL_FILE, {}).get("channel_id")

def save_balances():
    save_json(DATA_FILE, balances)

def save_channel(channel_id):
    save_json(CHANNEL_FILE, {"channel_id": channel_id})

# ----- BOT SETUP -----
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ----- HELPER -----
async def send_temp_message(ctx, content, delay=30, countdown=True):
    msg = await ctx.send(f"{content}\n⏳ Tin nhắn sẽ xoá sau {delay} giây.")
    for i in range(delay - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            await msg.edit(content=f"{content}\n⏳ Còn {i} giây...")
        except:
            break
    try:
        await ctx.message.delete()
        await msg.delete()
    except:
        pass

# ----- EVENTS -----
@bot.event
async def on_ready():
    print(f"✅ Bot đăng nhập với tên: {bot.user}")

# ----- COMMANDS -----
@bot.command()
async def set(ctx, mode: str, channel_id: int):
    if mode.lower() == "taixiu":
        save_channel(channel_id)
        global allowed_channel
        allowed_channel = channel_id
        await send_temp_message(ctx, f"✅ Bot sẽ hoạt động trong <#{channel_id}>")

@bot.command()
async def balance(ctx):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    user_id = str(ctx.author.id)
    balances.setdefault(user_id, 1000)
    save_balances()
    await send_temp_message(ctx, f"💰 Số dư: {balances[user_id]} 💰")

@bot.command()
async def nap(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    if not ctx.author.guild_permissions.administrator:
        return await send_temp_message(ctx, "🚫 Bạn không có quyền.")

    uid = str(member.id)
    balances.setdefault(uid, 1000)
    balances[uid] += amount
    save_balances()
    await send_temp_message(ctx, f"✅ Đã nạp {amount} 💰 cho {member.mention}")

@bot.command()
async def chuyen(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return

    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)
    balances.setdefault(sender_id, 1000)
    balances.setdefault(receiver_id, 1000)

    if amount <= 0 or balances[sender_id] < amount:
        return await send_temp_message(ctx, "❌ Không đủ số dư.")

    balances[sender_id] -= amount
    balances[receiver_id] += amount
    save_balances()
    await send_temp_message(ctx, f"🔁 {ctx.author.mention} đã chuyển {amount} 💰 cho {member.mention}")

@bot.command()
async def taixiu(ctx, amount: int, choice: str):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    uid = str(ctx.author.id)
    balances.setdefault(uid, 1000)

    if amount <= 0 or amount > balances[uid]:
        return await send_temp_message(ctx, "❌ Không hợp lệ.")

    if choice.lower() not in ["tài", "xỉu"]:
        return await send_temp_message(ctx, "❌ Chỉ chọn `Tài` hoặc `Xỉu`.")

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total >= 11 else "xỉu"

    if result == choice.lower():
        balances[uid] += amount
        outcome = "🎉 Bạn THẮNG!"
    else:
        balances[uid] -= amount
        outcome = "💀 Bạn THUA!"

    save_balances()
    await send_temp_message(
        ctx,
        f"🎲 Kết quả: {' + '.join(map(str, dice))} = {total} → **{result.upper()}**\n{outcome}\n💰 Số dư: {balances[uid]}"
    )

@bot.command()
async def thachdau(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return

    challenger = ctx.author
    balances.setdefault(str(challenger.id), 1000)
    balances.setdefault(str(member.id), 1000)

    if amount <= 0 or balances[str(challenger.id)] < amount or balances[str(member.id)] < amount:
        return await send_temp_message(ctx, "❌ Không đủ số dư.")

    countdown_time = 30
    msg = await ctx.send(
        f"⚔️ {challenger.mention} thách đấu {member.mention} {amount} 💰!\n"
        f"{member.mention}, bấm ✅ để chấp nhận hoặc ❌ để từ chối.\n"
        f"⏳ Thời gian còn lại: {countdown_time} giây..."
    )
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == member and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

    async def countdown():
        nonlocal countdown_time
        while countdown_time > 0:
            await asyncio.sleep(1)
            countdown_time -= 1
            try:
                await msg.edit(content=f"⚔️ {challenger.mention} thách đấu {member.mention} {amount} 💰!\n"
                                       f"{member.mention}, bấm ✅ hoặc ❌.\n"
                                       f"⏳ Thời gian còn lại: {countdown_time} giây...")
            except:
                break

    countdown_task = asyncio.create_task(countdown())

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        countdown_task.cancel()

        if str(reaction.emoji) == "✅":
            winner = random.choice([challenger, member])
            loser = member if winner == challenger else challenger

            balances[str(winner.id)] += amount
            balances[str(loser.id)] -= amount
            save_balances()
            result_msg = await ctx.send(f"🏆 {winner.mention} đã thắng và nhận {amount} 💰!")
        else:
            result_msg = await ctx.send(f"❌ {member.mention} đã từ chối.")
    except asyncio.TimeoutError:
        countdown_task.cancel()
        result_msg = await ctx.send(f"⌛ {member.mention} không phản hồi.")

    await asyncio.sleep(10)
    try:
        await ctx.message.delete()
        await msg.delete()
        await result_msg.delete()
    except:
        pass

# ----- START BOT -----
keep_alive()
bot.run(TOKEN)
