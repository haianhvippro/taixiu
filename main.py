import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
import random
from flask import Flask
from threading import Thread



# ----- CONFIGURATION -----
TOKEN = "MTMzMzA3MDMzNjc0ODQyMTE5Mg.Gx3IGz.6wccV-gCWA9ChTL9jxvKjG5lyYan5yXjwrNIKo"  # Thay bằng token thật của bạn
DATA_FILE = "balances.json"
CHANNEL_FILE = "channel.json"


# ----- LOAD & SAVE DATA -----
def load_balances():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_balances():
    with open(DATA_FILE, "w") as f:
        json.dump(balances, f)


def load_channel():
    if not os.path.exists(CHANNEL_FILE):
        return None
    with open(CHANNEL_FILE, "r") as f:
        return json.load(f).get("channel_id")


def save_channel(channel_id):
    with open(CHANNEL_FILE, "w") as f:
        json.dump({"channel_id": channel_id}, f)


# ----- BOT SETUP -----
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

balances = load_balances()
allowed_channel = load_channel()


# ----- HELPER -----
async def send_temp_message(ctx, content, delay=30, countdown=True):
    """
    Gửi tin nhắn tạm thời có hiển thị đếm ngược từng giây.
    """
    msg = await ctx.send(f"{content}\n⏳ Tin nhắn này sẽ tự xoá sau {delay} giây.")

    if countdown:
        for i in range(delay - 1, -1, -1):
            await asyncio.sleep(1)
            try:
                await msg.edit(content=f"{content}\n⏳ Còn {i} giây...")
            except:
                break
    else:
        await asyncio.sleep(delay)

    try:
        await ctx.message.delete()
        await msg.delete()
    except:
        pass




# ----- EVENTS -----
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập với tên: {bot.user}")


# ----- COMMANDS -----
@bot.command()
async def set(ctx, mode: str, channel_id: int):
    if mode.lower() == "taixiu":
        save_channel(channel_id)
        global allowed_channel
        allowed_channel = channel_id
        await send_temp_message(
            ctx, f"✅ Bot sẽ chỉ hoạt động trong kênh <#{channel_id}>")


@bot.command()
async def balance(ctx):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    user_id = str(ctx.author.id)
    balances.setdefault(user_id, 1000)
    save_balances()
    await send_temp_message(ctx, f"💰 Số dư của bạn: {balances[user_id]} 💰")


@bot.command()
async def nap(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    if not ctx.author.guild_permissions.administrator:
        return await send_temp_message(
            ctx, "🚫 Bạn không có quyền để sử dụng lệnh này.")
    user_id = str(member.id)
    balances.setdefault(user_id, 1000)
    balances[user_id] += amount
    save_balances()
    await send_temp_message(
        ctx,
        f"💰 Đã nạp {amount} 💰 cho {member.mention}. Số dư: {balances[user_id]} 💰"
    )


@bot.command()
async def chuyen(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)
    balances.setdefault(sender_id, 1000)
    balances.setdefault(receiver_id, 1000)

    if amount <= 0 or balances[sender_id] < amount:
        return await send_temp_message(
            ctx, "❌ Số tiền không hợp lệ hoặc không đủ số dư.")

    balances[sender_id] -= amount
    balances[receiver_id] += amount
    save_balances()
    await send_temp_message(
        ctx,
        f"🔁 {ctx.author.mention} đã chuyển {amount} 💰 cho {member.mention}.")


@bot.command()
async def taixiu(ctx, amount: int, choice: str):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return

    user_id = str(ctx.author.id)
    balances.setdefault(user_id, 1000)

    if amount <= 0 or amount > balances[user_id]:
        return await send_temp_message(
            ctx, f"❌ Số tiền không hợp lệ. Số dư: {balances[user_id]}")

    if choice.lower() not in ["tài", "xỉu"]:
        return await send_temp_message(ctx, "❌ Chọn `Tài` hoặc `Xỉu`.")

    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total >= 11 else "xỉu"

    message = f"🎲 {dice[0]} + {dice[1]} + {dice[2]} = {total} → **{result.upper()}**\n"

    if choice.lower() == result:
        balances[user_id] += amount
        message += f"🎉 Bạn THẮNG! Nhận {amount} 💰."
    else:
        balances[user_id] -= amount
        message += f"💀 Bạn THUA! Mất {amount} 💰."

    message += f"\n💼 Số dư hiện tại: {balances[user_id]} 💰"

    save_balances()
    await send_temp_message(ctx, message)


@bot.command()
async def thachdau(ctx, member: discord.Member, amount: int):
    if allowed_channel and ctx.channel.id != allowed_channel:
        return

    challenger_id = str(ctx.author.id)
    opponent_id = str(member.id)

    balances.setdefault(challenger_id, 1000)
    balances.setdefault(opponent_id, 1000)

    if amount <= 0 or balances[challenger_id] < amount or balances[opponent_id] < amount:
        return await send_temp_message(ctx, "❌ Không đủ số dư hoặc số tiền không hợp lệ.")

    countdown_time = 30

    msg = await ctx.send(
        f"⚔️ {ctx.author.mention} thách đấu {member.mention} với {amount} 💰!\n"
        f"{member.mention}, hãy bấm ✅ (đồng ý) hoặc ❌ (từ chối).\n"
        f"⏳ Thời gian còn lại: **{countdown_time}** giây..."
    )
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return (
            user == member
            and str(reaction.emoji) in ["✅", "❌"]
            and reaction.message.id == msg.id
        )

    # Tạo countdown cập nhật từng giây
    async def countdown():
        nonlocal countdown_time
        while countdown_time > 0:
            await asyncio.sleep(1)
            countdown_time -= 1
            try:
                await msg.edit(
                    content=f"⚔️ {ctx.author.mention} thách đấu {member.mention} với {amount} 💰!\n"
                            f"{member.mention}, hãy bấm ✅ (đồng ý) hoặc ❌ (từ chối).\n"
                            f"⏳ Thời gian còn lại: **{countdown_time}** giây..."
                )
            except:
                break

    # Chạy countdown song song với chờ phản hồi
    countdown_task = asyncio.create_task(countdown())

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        countdown_task.cancel()  # Dừng countdown khi có phản hồi

        if str(reaction.emoji) == "✅":
            winner = random.choice([ctx.author, member])
            loser = member if winner == ctx.author else ctx.author

            balances[str(winner.id)] += amount
            balances[str(loser.id)] -= amount
            save_balances()

            result_msg = await ctx.send(f"🏆 {winner.mention} đã thắng và nhận {amount} 💰!")
        else:
            result_msg = await ctx.send(f"❌ {member.mention} đã từ chối lời thách đấu.")

    except asyncio.TimeoutError:
        countdown_task.cancel()
        result_msg = await ctx.send(f"⌛ {member.mention} không phản hồi. Thách đấu bị huỷ.")

    # Xoá tin nhắn sau 10 giây
    await asyncio.sleep(10)
    try:
        await ctx.message.delete()
        await msg.delete()
        await result_msg.delete()
    except:
        pass






# ----- RUN -----
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot đang chạy!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
keep_alive()
bot.run(TOKEN)

def start_bot():
    bot.run(TOKEN)

# Chạy bot trong luồng phụ
t1 = Thread(target=start_bot)
t1.start()

# Flask là tiến trình chính
keep_alive()

