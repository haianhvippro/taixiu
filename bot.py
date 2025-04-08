import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os

# Load token từ file .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Tạo biến lưu số dư người chơi
balances = {}

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập với tên: {bot.user}")

@bot.command()
async def taixiu(ctx, bet_amount: int, bet: str):
    user_id = str(ctx.author.id)
    
    # Khởi tạo số dư nếu người chơi chưa có
    if user_id not in balances:
        balances[user_id] = 1000  # Mỗi người chơi bắt đầu với 1000 tiền

    bet = bet.lower()
    
    # Kiểm tra cú pháp cược
    if bet not in ["tài", "xỉu"]:
        await ctx.send("❌ Sai cú pháp! Dùng: `!taixiu <số tiền cược> <Tài/Xỉu>`")
        return
    
    # Kiểm tra số tiền cược hợp lệ
    if bet_amount <= 0:
        await ctx.send("❌ Số tiền cược phải lớn hơn 0.")
        return
    
    if bet_amount > balances[user_id]:
        await ctx.send(f"❌ Bạn không đủ tiền! Số dư hiện tại: {balances[user_id]} 💰")
        return

    # Quay xí ngầu
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tài" if total >= 11 else "xỉu"

    # Xử lý kết quả cược
    message = f"🎲 {dice[0]} + {dice[1]} + {dice[2]} = **{total}** → **{result.upper()}**\n"
    
    if bet == result:
        winnings = bet_amount  # Người chơi thắng, nhận lại tiền cược
        balances[user_id] += winnings
        message += f"🎉 Bạn **THẮNG** rồi! Bạn nhận được {winnings} 💰. Số dư mới: {balances[user_id]} 💰"
    else:
        balances[user_id] -= bet_amount  # Người chơi thua, mất tiền cược
        message += f"💀 Bạn **THUA** mất rồi! Bạn đã mất {bet_amount} 💰. Số dư còn lại: {balances[user_id]} 💰"
    
    # Gửi thông báo kết quả cược
    message += "\n**-----------------------------------------------------------**\n"
    message += "`(- Hãy ủng hộ tôi -)`\n"
    message += "**-----------------------------------------------------------**\n"
    await ctx.send(message)

# Chạy bot
bot.run(TOKEN)