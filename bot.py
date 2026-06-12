import discord
from discord.ext import commands
import os
import asyncio
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

    # 調整：新增接收 view_obj 參數
    def __init__(self, original_message: discord.Message, view_obj: discord.ui.View):
        super().__init__(timeout=None)
        self.original_message = original_message
        self.view_obj = view_obj

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("已回報完成給老闆！", ephemeral=True)

        owner = await interaction.client.fetch_user(MY_USER_ID)
        await owner.send(f"✅ **{interaction.user.display_name} 已完成剪輯！**\n🔗 連結: {self.link.value}")
        
        # 新增：把狀態標記為已完成，這樣等一下計時器到了就不會亂催稿
        self.view_obj.is_finished = True
        
        try:
            finished_embed = discord.Embed(
                title="🎬 今日剪輯任務",
                description="✅ 本期剪輯任務已結束，辛苦了！",
                color=discord.Color.secondary()
            )
            
            old_view = discord.ui.View.from_message(self.original_message)
            for item in old_view.children:
                item.disabled = True
                
            await self.original_message.edit(embed=finished_embed, view=old_view)
        except Exception as e:
            print(f"修改頻道訊息時發生錯誤: {e}")

class AttendanceView(discord.ui.View):
    def __init__(self, drive_link: str = ""):
        super().__init__(timeout=None)
        self.drive_link = drive_link  # 儲存老闆輸入的網址
        self.is_finished = False      # 記錄這項任務是不是完成了

    @discord.ui.button(label="開始剪輯", style=discord.ButtonStyle.green, custom_id="start_work_button")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 修正：如果機器人重啟過，從當前訊息的雲端硬碟連結提取網址，確保不遺失
        link = self.drive_link
        if not link and interaction.message.embeds and interaction.message.embeds[0].url:
            link = interaction.message.embeds[0].url

        owner = await interaction.client.fetch_user(MY_USER_ID)
        # 終極關鍵修正：把漏掉的格式補正，文字才不會報錯崩潰！
        await owner.send(f"🚀 **{interaction.user.display_name}** 開始剪輯了！")
        
        # 為了保證重啟後按鈕依然拿得到網址，從 Embed url 備份中讀取
        current_link = link if link else "請查看當前任務雲端硬碟連結"
        msg = f"✅ 已通知老闆你開始工作了！\n📁 **今日素材雲端連結：** {current_link}"
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="完成任務", style=discord.ButtonStyle.primary, custom_id="finish_work_button")
    async def finish_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FinishModal(original_message=interaction.message, view_obj=self))

# 給老闆填寫素材網址與時間的彈出視窗
class SetupModal(discord.ui.Modal, title='發布今日剪輯任務'):
    link = discord.ui.TextInput(label='請輸入今日素材雲端連結 1', style=discord.TextStyle.short, placeholder='https://drive.google.com/...', required=True)
    time_limit = discord.ui.TextInput(label='請輸入限時時間（單位：分鐘）', style=discord.TextStyle.short, placeholder='例如: 45', required=True)

    def __init__(self, setup_message: discord.Message):
        super().__init__(timeout=None)
        self.setup_message = setup_message

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            await self.setup_message.delete()
        except Exception as e:
            print(f"刪除設定按鈕訊息失敗: {e}")

        try:
            minutes = int(self.time_limit.value)
        except ValueError:
            minutes = 60

        total_seconds = minutes * 60  # 轉成總秒數
        role = interaction.guild.get_role(EDITOR_ROLE_ID)
        
        # 修正：把 link.value 直接塞進 Embed 的 url 屬性裡
        embed = discord.Embed(
            title="🎬 今日剪輯任務 (點此可直接開啟雲端)",
            url=self.link.value,
            description=f"請各位剪輯師開始打卡工作\n⏳ **本期任務限時倒數: {minutes:02d}:00**",
            color=discord.Color.blue()
        )
        msg = f"{role.mention if role else '未設定剪輯師身分組'}"
        
        attendance_view = AttendanceView(drive_link=self.link.value)
        # 記錄發出去的打卡面板訊息物件
        task_message = await interaction.channel.send(content=msg, embed=embed, view=attendance_view)

        # 終極修正：改為每分鐘更新一次，徹底解決 Discord 阻斷交互的問題
        async def countdown_task(msg_obj: discord.Message, view_obj: AttendanceView, role_obj, total_minutes: int):
            minutes_left = total_minutes
            
            while minutes_left > 0:
                if view_obj.is_finished:
                    return  # 如果剪輯師完成任務，立刻結束倒數
                
                # 改成每 60 秒才 edit 一次訊息，不再每秒疲勞轟炸 Discord 伺服器
                await asyncio.sleep(60)
                minutes_left -= 1
                
                if view_obj.is_finished:
                    return
                
                # 修正：倒數更新時也要保留 url，按鈕和超連結才不會跑掉
                countdown_embed = discord.Embed(
                    title="🎬 今日剪輯任務 (點此可直接開啟雲端)",
                    url=view_obj.drive_link,
                    description=f"請各位剪輯師開始打卡工作\n⏳ **本期任務限時倒數: {minutes_left:02d}:00**",
                    color=discord.Color.blue()
                )
                try:
                    await msg_obj.edit(embed=countdown_embed, view=view_obj)
                except Exception:
                    break  # 防止訊息被刪除時噴錯

            # 倒數結束：若依然未完成則執行催促
            if not view_obj.is_finished:
                mention_msg = f"⚠️ {role_obj.mention if role_obj else '@剪輯師'} 時間已到！任務逾時未完成，請儘速處理！"
                await msg_obj.channel.send(mention_msg)

        # 啟動非同步倒數（注意：這裡最後一個參數我們直接傳入的 minutes）
        asyncio.create_task(countdown_task(task_message, attendance_view, role, minutes))

# 老闆專用的啟動檢視按鈕
class AdminSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        
    @discord.ui.button(label="點擊設定今日素材網址", style=discord.ButtonStyle.danger)
    async def admin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("你沒有權限使用此按鈕。", ephemeral=True)
        
        # 把當前的訊息 (interaction.message) 傳進 Modal 裡
        await interaction.response.send_modal(SetupModal(setup_message=interaction.message))

@bot.command()
async def work(ctx):
    if not (ctx.author.guild_permissions.administrator):
        return await ctx.send("你沒有權限使用此指令。")
        
    # 乾乾淨淨：只在當前頻道發送紅色設定按鈕，不留任何多餘的提示文字或私訊
    await ctx.send(view=AdminSetupView())
    await ctx.message.delete()  # 刪除原指令 !work 字串，保持頻道乾淨

@bot.event
async def on_ready():
    # 註冊固定 custom_id 的按鈕 View，讓重啟後的按鈕依然有效
    bot.add_view(AttendanceView())
    print(f'機器人已上線: {bot.user}')
    
    # 新增：機器人重新部署上線後，自動發送通知並 @ 你
    try:
        # 1. 抓取你的使用者物件
        owner = await bot.fetch_user(MY_USER_ID)
        
        # 2. 設定你要接收通知的 Discord 頻道 ID（請將下方的 123456789 換成你當前工作頻道的 ID）
        # 提示：對著你的文字頻道按右鍵 -> 複製 ID
        NOTIFICATION_CHANNEL_ID = 123456789012345678  
        
        channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
        if channel:
            # 在指定頻道發送通知並標記你
            await channel.send(f"🚀 {owner.mention} 機器人已重新部署完成並成功上線！")
        else:
            # 如果找不到頻道，改用私訊通知你
            await owner.send("🚀 機器人已重新部署完成並成功上線！")
            
    except Exception as e:
        print(f"發送上線通知時發生錯誤: {e}")

# 在機器人登入前先把虛擬網頁跑起來
keep_alive()

bot.run(TOKEN)
