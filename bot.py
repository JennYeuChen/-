import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# 1. 在這裡讀取 .env 檔案
load_dotenv()

# 2. 在這裡取得 Token
TOKEN = os.getenv('DISCORD_TOKEN')

# 設定機器人權限
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# 導入你剛剛設計的按鈕類別
class AttendanceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="開始工作", style=discord.ButtonStyle.green, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"✅ {interaction.user.display_name} 開始剪輯了！", ephemeral=True)

# 機器人啟動時觸發
@bot.event
async def on_ready():
    # 3. 在這裡註冊你的持久化按鈕 (重要！)
    bot.add_view(AttendanceView())
    print(f'機器人已登入為 {bot.user}')

# 4. 在這裡啟動機器人 (Token 的最後歸宿)
bot.run(TOKEN)
