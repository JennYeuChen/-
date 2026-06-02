import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# 讀取環境變數 (TOKEN 放在 .env 檔)
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定 Intent (這是機器人讀取訊息所需的權限)
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# 按鈕類別
class AttendanceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # 讓按鈕永遠有效

    @discord.ui.button(label="開始剪輯", style=discord.ButtonStyle.green, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🚀 {interaction.user.display_name} 開始工作了！", ephemeral=True)
        # 這裡未來會接 Notion API

# 招喚指令
@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    embed = discord.Embed(
        title="🎬 影片製作工作台",
        description="點擊下方按鈕以開始或回報進度。",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=AttendanceView())

@bot.event
async def on_ready():
    # 重新載入按鈕邏輯，確保重啟後按鈕依然有效
    bot.add_view(AttendanceView())
    print(f'機器人已上線: {bot.user}')

bot.run(TOKEN)
