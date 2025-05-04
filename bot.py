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

# Lệnh kiểm tra số dư
@bot.command()
async def balance(ctx):
    user_id = str(ctx.author.id)
    
    if user_id not in balances:
        balances[user_id] = 1000  # Mặc định số dư nếu người chơi chưa có

    await ctx.send(f"💰 Số dư của bạn: {balances[user_id]} 💰")

@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập với tên: {bot.user} | bây giờ tôi muốn bù khu cầu quá đi cậu chủ của tôi 😋 😋")

@bot.command()
async def taixiu(ctx, *args):
    user_id = str(ctx.author.id)

    # Kiểm tra nếu người chơi chưa có số dư
    if user_id not in balances:
        balances[user_id] = 1000  # Mỗi người chơi bắt đầu với 1000 tiền

    # Kiểm tra cú pháp: Đảm bảo có đúng 2 tham số (số tiền cược và Tài/Xỉu)
    if len(args) != 2:
        await ctx.send("❌ Lỗi cú pháp! Đúng cú pháp là `!taixiu <số tiền cược> <Tài/Xỉu>`. Bạn thiếu tham số.")
        return

    # Kiểm tra số tiền cược phải là một số
    try:
        bet_amount = int(args[0])  # Số tiền cược
    except ValueError:
        await ctx.send("❌ Lỗi cú pháp! Số tiền cược phải là một số hợp lệ.")
        return

    # Kiểm tra cú pháp: Tài/Xỉu phải là tham số thứ hai
    bet = args[1].lower()

    if bet not in ["tài", "xỉu"]:
        await ctx.send("❌ Lỗi cú pháp! Bạn phải chọn giữa `Tài` và `Xỉu`.") 
        return

    # Kiểm tra số tiền cược hợp lệ
    if bet_amount <= 0:
        await ctx.send("❌ Lỗi cú pháp! Số tiền cược phải lớn hơn 0.")
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
    
    message += "\n**---------------------------------------------------------------------------------------------------------------**\n"
    message += "```diff\n- --- Hãy ủng hộ tôi qua ---\n```"
    message += "**`- ----- stk:22221042009 -----`**\n"  
    message += "**`- ----------MB bank----------`**\n"  
    message += "**-----------------------------------------------------------------------------------------------------------------**\n"
    await ctx.send(message)

# Lệnh nạp tiền
# Lệnh nạp tiền - chỉ quản trị viên mới có thể sử dụng
@bot.command()
@commands.has_permissions(administrator=True)
async def nap(ctx, member: discord.Member, amount: int):
    # Kiểm tra nếu số tiền nạp phải là một số dương
    if amount <= 0:
        await ctx.send("❌ Lỗi cú pháp! Số tiền nạp phải lớn hơn 0.")
        return

    # Kiểm tra nếu người chơi đã có số dư, nếu không thì khởi tạo số dư là 1000
    user_id = str(member.id)
    if user_id not in balances:
        balances[user_id] = 1000  # Nếu chưa có số dư, khởi tạo mặc định là 1000

    # Cập nhật số dư của người chơi
    balances[user_id] += amount
    await ctx.send(f"💰 Đã nạp {amount} 💰 cho {member.mention}. Số dư của họ hiện tại là {balances[user_id]} 💰")

# Bắt lỗi nếu người không có quyền cố sử dụng lệnh
@nap.error
async def nap_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Bạn không có quyền để sử dụng lệnh này.")

# Chạy bot
bot.run(TOKEN)

