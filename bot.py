import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_USER_ID = 1150359752359038986  # ⚠️ 請將此處改成你的 Discord ID，用於接收私訊
EDITOR_ROLE_ID = 1492191110477516912  # ⚠️ 請將此處換成你的真實剪輯師身分組 ID

# 建立一個簡單的網頁伺服器，防止 Render 睡眠
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    # Render 會自動提供 PORT 環境變換，讀不到就預設 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 完成任務時的彈出視窗
class FinishModal(discord.ui.Modal, title='回報剪輯完成'):
    link = discord.ui.TextInput(label='請輸入完成後的雲端連結', style=discord.TextStyle.short, placeholder='https://drive.google.com/...', required=True)

    # 讓 Modal 在建立時，可以把當前的 message 記下來
    def __init__(self, original_message: discord.Message):
        super().__init__(timeout=None)
        self.original_message = original_message

    async def on_submit(self, interaction: discord.Interaction):
        # 1. 優先回應 Discord，避免互動超時（通知剪輯師已送出）
        await interaction.response.send_message("已回報完成給老闆！", ephemeral=True)

        # 2. 私訊通知老闆
        owner = await interaction.client.fetch_user(MY_USER_ID)
        await owner.send(f"✅ **{interaction.user.display_name} 已完成剪輯！**\n🔗 連結: {self.link.value}")
        
        # 3. 安全地修改頻道中原本的 Embed 狀態
        try:
            # 修改後：直接把結束訊息寫在 description，不使用 field
            finished_embed = discord.Embed(
                title="🎬 今日剪輯任務",
                description="✅ 本期剪輯任務已結束，辛苦了！",
                color=discord.Color.secondary()
            )
            
            # 取得原本的按鈕並全部停用
            old_view = discord.ui.View.from_message(self.original_message)
            for item in old_view.children:
                item.disabled = True
                
            # 使用原本的 message 物件直接做 edit
            await self.original_message.edit(embed=finished_embed, view=old_view)
        except Exception as e:
            print(f"修改頻道訊息時發生錯誤: {e}")

class AttendanceView(discord.ui.View):
    def __init__(self, drive_link: str = ""):
        super().__init__(timeout=None)
        self.drive_link = drive_link  # 儲存老闆輸入的網址

    @discord.ui.button(label="開始剪輯", style=discord.ButtonStyle.green, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        owner = await interaction.client.fetch_user(MY_USER_ID)
        await owner.send(f"🚀 **{interaction.user.display_name} 開始剪輯了！**")
        
        # 按下開始剪輯後，才私密顯示網址給該剪輯師
        msg = f"✅ 已通知老闆你開始工作了！\n📁 **今日素材雲端連結：** {self.drive_link}"
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="完成任務", style=discord.ButtonStyle.primary, custom_id="finish_work")
    async def finish_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 把當下的互動訊息 (interaction.message) 傳進 Modal 裡
        await interaction.response.send_modal(FinishModal(original_message=interaction.message))

# 給老闆填寫素材網址的彈出視窗
class SetupModal(discord.ui.Modal, title='發布今日剪輯任務'):
    link = discord.ui.TextInput(label='請輸入今日素材雲端連結 1', style=discord.TextStyle.short, placeholder='https://drive.google.com/...', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(EDITOR_ROLE_ID)
        
        # 修改後：只保留標題與敘述，畫面更乾淨
        embed = discord.Embed(title="🎬 今日剪輯任務", description="請各位剪輯師開始打卡工作", color=discord.Color.blue())
        
        msg = f"{role.mention if role else '未設定剪輯師身分組'}"
        await interaction.response.send_message(content=msg, embed=embed, view=AttendanceView(drive_link=self.link.value))

# 老闆專用的啟動檢視按鈕
class AdminSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="點擊設定今日素材網址", style=discord.ButtonStyle.danger)
    async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("你沒有權限使用此按鈕。", ephemeral=True)
        await interaction.response.send_modal(SetupModal())

@bot.command()
async def work(ctx):
    if not (ctx.author.guild_permissions.administrator):
        return await ctx.send("你沒有權限使用此指令。")
        
    # 發送一個暫時的管理員按鈕，讓你點擊彈出視窗
    await ctx.send("請點擊下方按鈕以輸入今天的雲端硬碟網址：", view=AdminSetupView(), delete_after=60)
    await ctx.message.delete()  # 刪除原指令字串，保持頻道乾淨

@bot.event
async def on_ready():
    bot.add_view(AttendanceView())  # 注意：這裡不要傳參數，保持預設空值
    print(f'機器人已上線: {bot.user}')

# 在機器人登入前先把虛擬網頁跑起來
keep_alive()

bot.run(TOKEN)
