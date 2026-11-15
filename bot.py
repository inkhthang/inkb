import discord
from discord.ext import commands

# Cấu hình Bot Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# --- CẤU HÌNH ID (Thay đổi các ID này theo server của bạn) ---
CREATE_CHANNEL_ID = 1571349675301146655  # ID của kênh thoại "➕ . Create Voice"
CATEGORY_ID = 1571165646530814063       # ID của danh mục (Category) chứa các phòng riêng tư

# Lưu trữ tạm thời: {channel_id: owner_id}
owned_channels = {}

class RoomControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    # --- KHÓA PHÒNG ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="lock_room")
    async def lock_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 Đã khóa phòng thành công!", ephemeral=True)

    # --- MỞ KHÓA PHÒNG ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔓", custom_id="unlock_room")
    async def unlock_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        await channel.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.response.send_message("🔓 Đã mở khóa phòng thành công!", ephemeral=True)

    # --- GIỚI HẠN SỐ NGƯỜI ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="👥", custom_id="limit_room")
    async def limit_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(LimitModal())

    # --- ĐỔI TÊN PHÒNG ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="📝", custom_id="rename_room")
    async def rename_room(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(RenameModal())

    # --- MUTE THÀNH VIÊN ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔇", custom_id="mute_user")
    async def mute_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(TargetUserModal("mute"))

    # --- UNMUTE THÀNH VIÊN ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🎤", custom_id="unmute_user")
    async def unmute_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(TargetUserModal("unmute"))

    # --- BAN (CHẶN) THÀNH VIÊN ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🚫", custom_id="ban_user")
    async def ban_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(TargetUserModal("ban"))

    # --- UNBAN (BỎ CHẶN) THÀNH VIÊN ---
    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="➕", custom_id="unban_user")
    async def unban_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("❌ Bạn cần phải đang ở trong phòng thoại!", ephemeral=True)
            return
        await interaction.response.send_modal(TargetUserModal("unban"))
# --- CÁC MODAL (BẢNG NHẬP LIỆU) ---

class RenameModal(discord.ui.Modal, title="Đổi tên phòng"):
    new_name = discord.ui.TextInput(label="Tên phòng mới", placeholder="Nhập tên phòng...", max_length=50)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel
        await channel.edit(name=self.new_name.value)
        await interaction.response.send_message(f"✅ Đã đổi tên phòng thành: **{self.new_name.value}**", ephemeral=True)

class LimitModal(discord.ui.Modal, title="Giới hạn số lượng thành viên"):
    limit = discord.ui.TextInput(label="Số người tối đa (0-99)", placeholder="Nhập số...", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.limit.value)
            if 0 <= val <= 99:
                channel = interaction.user.voice.channel
                await channel.edit(user_limit=val)
                await interaction.response.send_message(f"✅ Đã đặt giới hạn phòng thành: **{val}** người", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Vui lòng nhập số từ 0 đến 99.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Giá trị không hợp lệ!", ephemeral=True)

class TargetUserModal(discord.ui.Modal):
    def __init__(self, action: str):
        self.action = action
        titles = {"mute": "Chặn micro thành viên", "unmute": "Bỏ chặn micro", "ban": "Đuổi & Chặn thành viên", "unban": "Bỏ chặn thành viên"}
        super().__init__(title=titles.get(action, "Quản lý thành viên"))
        
    username = discord.ui.TextInput(label="Tên tài khoản (Username) hoặc ID", placeholder="Nhập username chính xác...")

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.user.voice.channel
        guild = interaction.guild
        member = discord.utils.get(guild.members, name=self.username.value)
        
        if not member:
            await interaction.response.send_message("❌ Không tìm thấy thành viên này trong server!", ephemeral=True)
            return

        if self.action == "mute":
            await channel.set_permissions(member, speak=False)
            await interaction.response.send_message(f"🔇 Đã tắt mic của **{member.name}** trong phòng.", ephemeral=True)
        elif self.action == "unmute":
            await channel.set_permissions(member, speak=True)
            await interaction.response.send_message(f"🎤 Đã bật mic cho **{member.name}**.", ephemeral=True)
        elif self.action == "ban":
            await channel.set_permissions(member, connect=False)
            if member.voice and member.voice.channel == channel:
                await member.move_to(None) # Đuổi ra khỏi phòng nếu đang ở trong đó
            await interaction.response.send_message(f"🚫 Đã chặn **{member.name}** vào phòng.", ephemeral=True)
        elif self.action == "unban":
            await channel.set_permissions(member, connect=None)
            await interaction.response.send_message(f"✅ Đã bỏ chặn **{member.name}**.", ephemeral=True)

# --- XỬ LÝ SỰ KIỆN VOICE STATE ---

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # 1. Người dùng vào kênh tạo phòng
    if after.channel and after.channel.id == CREATE_CHANNEL_ID:
        guild = after.channel.guild
        category = guild.get_channel(CATEGORY_ID)
        
        # Tạo phòng riêng
        room_name = f"🎧 · {member.name}'s Room"
        new_channel = await guild.create_voice_channel(name=room_name, category=category)
        
        # Cấp quyền quản lý cho chủ phòng
        await new_channel.set_permissions(member, connect=True, manage_channels=True, speak=True)
        
        # Chuyển người dùng vào phòng mới tạo
        await member.move_to(new_channel)
        
        # Lưu lại chủ sở hữu
        owned_channels[new_channel.id] = member.id

    # 2. Kiểm tra khi rời phòng để xóa phòng trống
    if before.channel and before.channel.id in owned_channels:
        if len(before.channel.members) == 0:
            channel_id = before.channel.id
            del owned_channels[channel_id]
            await before.channel.delete()

# Lệnh gửi bảng điều khiển cố định ra kênh chat
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_panel(ctx):
    embed = discord.Embed(
        title="— · Private Rooms",
        description="Use the buttons below.\nJoin **➕ . Create Voice** to create a room.",
        color=discord.Color.from_rgb(114, 91, 142)
    )
    embed.add_field(
        name="Main settings:",
        value="• 🔒 — Close\n• 🔓 — Open\n• 👥 — Limit\n• 📝 — Rename",
        inline=False
    )
    embed.add_field(
        name="Access:",
        value="• 🔇 — Mute\n• 🎤 — Unmute\n• 🚫 — Ban\n• ➕ — Unban",
        inline=False
    )
    
    view = RoomControlView()
    await ctx.send(embed=embed, view=view)

# Chạy bot (Thay 'YOUR_BOT_TOKEN' bằng Token thực tế của bạn)
bot.run("MTUxNjM1MDk4MzcxNjg2NDEyMA.GpI7O4.a_3rbrISIdD1AvpdGu73GOyqB3u7Yu3vDCR7Z8")