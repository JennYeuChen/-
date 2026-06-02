import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定 Intents (這對讀取指令非常重要)
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

class AttendanceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="開始剪輯", style=discord.ButtonStyle.green, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ {interaction.user.display_name} 開始剪輯了！", ephemeral=True)

@bot.command()
async def setup(ctx):
    # 確保只有你可以使用這個指令
    if await bot.is_owner(ctx.author) or ctx.author.guild_permissions.administrator:
        view = AttendanceView()
        await ctx.send("🎬 **工作室打卡台**\n點擊下方按鈕開始工作：", view=view)
    else:
        await ctx.send("你沒有權限使用此指令。")

@bot.event
async def on_ready():
    bot.add_view(AttendanceView())
    print(f'機器人已上線: {bot.user}')

bot.run(TOKEN)
