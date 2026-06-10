import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MY_USER_ID = 1150359752359038986  # ⚠️ 請將此處改成你的 Discord ID，用於接收私訊

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 完成任務時的彈出視窗
class FinishModal(discord.ui.Modal, title='回報剪輯完成'):
    link = discord.ui.TextInput(label='請輸入完成後的雲端連結', style=discord.TextStyle.short, placeholder='https://drive.google.com/...', required=True)

    async def on_submit(self, interaction: discord.Interaction):
        owner = await interaction.client.fetch_user(MY_USER_ID)
        await owner.send(f"✅ **{interaction.user.display_name} 已完成剪輯！**\n🔗 連結: {self.link.value}")
        await interaction.response.send_message(f"已回報完成給老闆！", ephemeral=True)

class AttendanceView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="開始剪輯", style=discord.ButtonStyle.green, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        owner = await interaction.client.fetch_user(MY_USER_ID)
        await owner.send(f"🚀 **{interaction.user.display_name} 開始剪輯了！**")
        await interaction.response.send_message("已通知老闆你開始工作了！", ephemeral=True)

    @discord.ui.button(label="完成任務", style=discord.ButtonStyle.primary, custom_id="finish_work")
    async def finish_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FinishModal())

@bot.command()
async def work(ctx, role: discord.Role = None):
    # 用法: !work @剪輯師
    if not (ctx.author.guild_permissions.administrator):
        return await ctx.send("你沒有權限使用此指令。")
    
    embed = discord.Embed(title="🎬 今日剪輯任務", description="請各位剪輯師開始打卡工作", color=discord.Color.blue())
    embed.add_field(name="📁 素材雲端連結 1", value="[點擊此處取得素材](https://your-drive-link-1.com)", inline=False)
    
    msg = f"{role.mention if role else ''}"
    await ctx.send(content=msg, embed=embed, view=AttendanceView())

@bot.event
async def on_ready():
    bot.add_view(AttendanceView())
    print(f'機器人已上線: {bot.user}')

bot.run(TOKEN)
