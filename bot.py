import discord

class AttendanceView(discord.ui.View):
    def __init__(self):
        # 關鍵：timeout=None 讓按鈕永遠有效
        super().__init__(timeout=None)

    @discord.ui.button(label="開始工作", style=discord.ButtonStyle.primary, custom_id="start_work")
    async def start_work(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 這裡寫 Notion API 的呼叫
        # await notion_client.update_status(user=interaction.user.name, status="Working")
        
        await interaction.response.send_message(f"收到！{interaction.user.display_name} 開始剪輯影片了。", ephemeral=True)

# 當機器人啟動時執行
# bot.add_view(AttendanceView())