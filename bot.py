import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
import os
import database

from dotenv import load_dotenv


load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

database.setup()

REGION_CHOICES = [
    app_commands.Choice(name=r, value=r)
    for r in config.REGION_ROLES
]

RESOURCE_CHOICES = [
    app_commands.Choice(name=r, value=r)
    for r in config.RESOURCES
]

BUFF_TYPE_CHOICES = [
    app_commands.Choice(name=buff_type.replace('_', ' ').title(), value=buff_type)
    for buff_type in config.BUFFS.keys()
]

staff = app_commands.Group(name="staff", description="Trade team commands")
bot.tree.add_command(staff)

# -------------------
# Helpers
# -------------------

def has_role(member, role):

    return any(r.name == role for r in member.roles)


def get_region(member):

    regions = [r.name for r in member.roles if r.name in config.REGION_ROLES]

    if len(regions) == 1:
        return regions[0]
    #handle dragonstaone/crownlands dual role
    if len(regions)== 2:
        if "Dragonstone" in regions:
            return regions[0] if regions[1] == "Crownlands" else regions[1]
    return None

async def log_channel(guild):

    for channel in guild.text_channels:
        if channel.name == config.TRADE_LOG_CHANNEL:
            return channel

async def save_edit_channel(guild):
    for channel in guild.text_channels:
        if channel.name == config.SAVE_EDIT_CHANNEL:
            return channel
# -------------------
# Ready
# -------------------

@bot.event
async def setup_hook():

    guild = discord.Object(id=config.GUILD_ID)

    # clear global commands
    #bot.tree.clear_commands(guild=None)
    #await bot.tree.sync()

    # clear guild commands
    bot.tree.clear_commands(guild=guild)


    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)

    print(f"Synced {len(synced)} commands to dev guild.")
    
@bot.event
async def on_ready():

    #weekly_production.start()
    #weekly_maintenance.start()

    print("Trade Bot Ready")

# -------------------
# STOCKPILE
# -------------------

#for player
@bot.tree.command(name="stockpile", description="View your region's stockpile")
async def stockpile(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE):

        await interaction.followup.send(
            "You need the Trade Charter role.",
            ephemeral=True
        )
        return

    region = get_region(interaction.user)

    if not region:

        await interaction.followup.send(
            "No valid region role found.",
            ephemeral=True
        )
        return

    data = database.get_stockpile(region)
    maintenance = config.MAINTENANCE.get(region, {})
    production = config.PRODUCTION.get(region, {})

    msg = f"**{region} Stockpile**\n"
    msg += "```"

    msg += f"{'Resource':<8}{'Current':>8}{'Maint':>8}{'Remain':>8}{'Production':>12}\n"
    msg += "-" * 45 + "\n"

    for resource, amount in data.items():
        maint = maintenance.get(resource, 0)
        remaining = amount - maint
        prod = production.get(resource, 0)

        msg += f"{resource:<8}{amount:>8}{maint:>8}{remaining:>8}{prod:>8}\n"

    msg += "```"

    print("STOCKPILE CALLED", region)

    await interaction.followup.send(msg, ephemeral=True)

#for staff

@staff.command(name="stockpile_region", description="View a specific region's stockpile")

@app_commands.describe(region="Region to inspect")

@app_commands.choices(
    region=REGION_CHOICES
)

async def stockpile_region(interaction: discord.Interaction, region: str):

    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.followup.send(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if region not in config.REGION_ROLES:

        await interaction.followup.send(
            "Invalid region.",
            ephemeral=True
        )
        return

    data = database.get_stockpile(region)

    msg = f"**{region} Stockpile**\n"

    for resource, amount in data.items():
        msg += f"{resource}: {amount}\n"
    
    print("STOCKPILE_REGION CALLED", region)

    await interaction.followup.send(msg, ephemeral=True)

# -------------------
# TRANSFER STOCKPILE CONFIRMATION
# -------------------

class TransferConfirm(discord.ui.View):

    def __init__(self, sender, receiver):
        super().__init__(timeout=30)

        self.sender = sender
        self.receiver = receiver

    @discord.ui.button(label="Confirm Transfer", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        database.transfer_stockpile(self.sender, self.receiver)

        msg = (
            f"{self.sender} ➜ {self.receiver}\n"
        )

        await interaction.response.edit_message(content=msg, view=None)

        log = await log_channel(interaction.guild)
        if log:
            await log.send("Stockpile Transfer\n" + msg + "\n=======================\n")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Transfer cancelled.",
            view=None
        )

# -------------------
# TRANSFER STOCKPILE
# -------------------

@staff.command(name="transfer_resources", description="Transfer all resources to another region")

@app_commands.describe(
    sender="Region sending resources",
    receiver="Region receiving resources"
)

@app_commands.choices(
    sender=REGION_CHOICES,
    receiver=REGION_CHOICES
)

async def transfer_resources(
    interaction: discord.Interaction,
    sender: str,
    receiver: str
):

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if sender == receiver:

        await interaction.response.send_message(
            "Cannot transfer to the same region.",
            ephemeral=True
        )
        return

    view = TransferConfirm(sender, receiver)

    msg = (
        f"Confirm Transfer\n\n"
        f"Sender: {sender}\n"
        f"Receiver: {receiver}\n"
    )

    await interaction.response.send_message(
        msg,
        view=view,
        ephemeral=True
    )

# -------------------
# BUY BUFF CONFIRMATION
# -------------------

class BuyBuffConfirm(discord.ui.View):

    def __init__(self, region, buff_type, tier, cost):
        super().__init__(timeout=30)

        self.region = region
        self.buff_type = buff_type
        self.tier = tier
        self.cost = cost

    @discord.ui.button(label="Confirm Purchase", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        for resource, amount in self.cost.items():
            database.change_resource(self.region, resource, -amount)

        database.set_buff(self.region, self.buff_type, self.tier)

        msg = f"Buff Purchased: {self.region} - {config.BUFFS[self.buff_type]['name']} ({self.tier})"

        await interaction.response.edit_message(content=msg, view=None)

        log = await log_channel(interaction.guild)
        if log:
            await log.send("```diff\n+" + msg + "```\n")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Purchase cancelled.",
            view=None
        )


# -------------------
# BUY BUFF COMMAND
# -------------------

@bot.tree.command(name="buy_buff", description="Purchase a buff tier for a region")

@app_commands.describe(
    buff_type="Type of buff",
    tier="Tier to purchase"
)

@app_commands.choices(
    buff_type=BUFF_TYPE_CHOICES,
    tier=[
        app_commands.Choice(name="Tier 1", value=1),
        app_commands.Choice(name="Tier 2", value=2),
        app_commands.Choice(name="Tier 3", value=3),
    ]
)

async def buy_buff(interaction: discord.Interaction, buff_type: str, tier: int):

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE):

        await interaction.response.send_message(
            "Charter only",
            ephemeral=True
        )
        return

    buff_data = config.BUFFS[buff_type]

    region = get_region(interaction.user)
    
    tier_name = list(buff_data["tiers"].keys())[tier - 1]

    cost = buff_data["tiers"][tier_name]["cost"]

    # check resources
    insufficient = []
    for resource, amount in cost.items():
        current = database.get_amount(region, resource)
        if current < amount:
            insufficient.append(f"{resource}: {current}/{amount}")

    if insufficient:
        msg = f"Insufficient resources:\n" + "\n".join(insufficient)
        await interaction.response.send_message(msg, ephemeral=True)
        return
    
    
    # confirmation
    view = BuyBuffConfirm(region, buff_type, tier, cost)

    msg = f"Confirm Buff Purchase\n\nRegion: {region}\nBuff: {buff_data['name']}\nTier: {tier}\nCost:\n"
    for resource, amount in cost.items():
        msg += f"{amount} {resource}\n"

    await interaction.response.send_message(
        msg,
        view=view,
        ephemeral=True
    )

# -------------------
# TRADE CONFIRMATION
# -------------------

class TradeConfirm(discord.ui.View):

    def __init__(self, sender, receiver, resource, amount, rp_link, comment=None):
        super().__init__(timeout=30)

        self.sender = sender
        self.receiver = receiver
        self.resource = resource
        self.amount = amount
        self.rp_link = rp_link
        self.comment = comment
        self.processed = False

    @discord.ui.button(label="Confirm Trade", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.processed:
            await interaction.response.send_message(
                "This trade is already being processed.",
                ephemeral=True
            )
            return

        self.processed = True

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Processing trade...",
            view=self
        )

        trade_id = database.log_trade(
            self.sender, self.receiver, self.resource, self.amount
        )

        if self.resource in config.RESOURCES:
            database.change_resource(self.sender, self.resource, -self.amount)
            database.change_resource(self.receiver, self.resource, self.amount)
        else:
            save_edit = await save_edit_channel(interaction.guild)
            if save_edit:
                if self.comment:
                    comment_text = f"\nComment: {self.comment}"
                else:
                    comment_text = ""
                await save_edit.send(
                    f"- Transfer {self.amount} gold from {self.sender} to {self.receiver} (Trade #{trade_id}){comment_text}"
                )

        msg = (
            f"{self.sender} ➜ {self.receiver}\n"
            f"{self.amount} {self.resource}\n"
            f"RP Link: {self.rp_link}"
        )

        if self.comment:
            msg += f"\nComment: {self.comment}"

        print("Trade confirmed:", self.sender, self.receiver, self.resource, self.amount)

        log = await log_channel(interaction.guild)
        if log:
            await log.send(f"Trade #{trade_id}\n{msg}\n=======================\n")

        await interaction.edit_original_response(
            content="Trade processed.",
            view=self
        )
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.processed:
            await interaction.response.send_message(
                "This trade is already being processed.",
                ephemeral=True
            )
            return

        self.processed = True

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="Trade cancelled.",
            view=None
        )

# -------------------
# TRADE COMMAND
# -------------------

@bot.tree.command(name="trade", description="Send resources to another region")
@app_commands.describe(
    receiver="Region receiving goods",
    resource="Resource type",
    amount="Amount to send",
    rp_link="Link to RP post",
    comment="Optional note about the trade"
)
@app_commands.choices(
    receiver=REGION_CHOICES,
    resource=RESOURCE_CHOICES + [app_commands.Choice(name="Gold", value="Gold")]
)
async def trade(
    interaction: discord.Interaction,
    receiver: str,
    resource: str,
    amount: int,
    rp_link: str,
    comment: str | None = None
):

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE):

        await interaction.response.send_message(
            "You lack Trade CHARTER.",
            ephemeral=True
        )
        return

    sender = get_region(interaction.user)

    if not sender:

        await interaction.response.send_message(
            "No valid region role found.",
            ephemeral=True
        )
        return

    if receiver == sender:

        await interaction.response.send_message(
            "Cannot trade with your own region.",
            ephemeral=True
        )
        return
    
    if resource in config.RESOURCES:
        current = database.get_amount(sender, resource)
        if current < amount:

            await interaction.response.send_message(
                f"{sender} only has {current} {resource}",
                ephemeral=True
            )
            return
        
    if amount <= 0:

        await interaction.response.send_message(
            "Don't try to steal!",
            ephemeral=True
        )
        return
    


    #check RP link format (basic check, can be improved)
    if rp_link not  in ["", None]:
        if not rp_link.startswith("https://discord.com") or rp_link.startswith("https://discordapp.com"):
            await interaction.response.send_message(
                "Invalid RP link format.",
                ephemeral=True
            )
            return
    else:
        await interaction.response.send_message(
            "No RP link provided. Please include a link to the RP post describing the trade.",
            ephemeral=True
        )
        return
    
    view = TradeConfirm(sender, receiver, resource, amount, rp_link, comment)

    msg = (
        f"Confirm Trade\n\n"
        f"Sender: {sender}\n"
        f"Receiver: {receiver}\n"
        f"Resource: {resource}\n"
        f"Amount: {amount}\n"
        f"RP Link: {rp_link}"
    )

    if comment:
        msg += f"\nComment: {comment}"

    await interaction.response.send_message(
        msg,
        view=view,
        ephemeral=True
    )

# -------------------
# MODIFY STOCKPILE
# -------------------

@staff.command(name="modify_stockpile", description="Modify a region's stockpile")

@app_commands.choices(
    region=REGION_CHOICES,
    resource=RESOURCE_CHOICES
)

async def modify_stockpile(
    interaction:discord.Interaction,
    region:str,
    resource:str,
    amount:int):

    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user,config.TRADE_TEAM_ROLE):

        await interaction.followup.send(
            "Trade Team only.",
            ephemeral=True
        )

        return
    print("MODSTOCK CALLED", region, resource, amount)
    database.change_resource(region,resource,amount)

    msg = f"{region} {resource} {'+' if amount>=0 else ''}{amount}"

    await interaction.followup.send(msg, ephemeral=True)

    log = await log_channel(interaction.guild)
    await log.send(f"Modified: {msg + "\n=======================\n"}")

# -------------------
# WEEKLY PRODUCTION
# -------------------
class ProductionConfirm(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Confirm Production", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        msg = "**Production Applied**\n"

        for region, resources in config.PRODUCTION.items():
            msg += f"**{region}**\n"
            for resource, amount in resources.items():

                database.change_resource(region, resource, amount)
                msg += f"{amount} {resource}\n"
            msg += "--------------------------\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)
        if log:
            await log.send(msg + "\n=======================\n")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Production cancelled.",
            view=None
        )

@tasks.loop(hours=168)
async def weekly_production():

    guild = bot.guilds[0]
    log = await log_channel(guild)

    msg = "**Weekly Production Applied**\n"

    for region, resources in config.PRODUCTION.items():

        for resource, amount in resources.items():

            database.change_resource(region, resource, amount)

            msg += f"{region}: +{amount} {resource}\n"

    if log:
        await log.send(msg+ "\n=======================\n")

@staff.command(name="production", description="Apply weekly production")

async def production(interaction: discord.Interaction):

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    msg = "**Confirm Production Cycle**\n\n"

    for region, resources in config.PRODUCTION.items():

        for resource, amount in resources.items():
            msg += f"{region}: +{amount} {resource}\n"

    await interaction.response.send_message(
        msg,
        view=ProductionConfirm(),
        ephemeral=True
    )
# -------------------
# WEEKLY MAINTENANCE
# -------------------

def calculate_debuffs(region):

    debuffs = {}

    for resource, data in config.DEBUFFS.items():

        amount = database.get_amount(region, resource)

        # simple thresholds (you can tweak later)
        if amount < -6:
            tier = 3
        elif amount < -3:
            tier = 2
        elif amount < 0:
            tier = 1
        else:
            tier = 0

        if tier > 0:
            debuffs[resource] = {
                "tier": tier,
                "name": data["tiers"][tier]["name"]
            }
        if amount < 0:
            database.set_amount(region, resource, 0)
    return debuffs

class MaintenanceConfirm(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Confirm Maintenance", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        msg = "**Maintenance Applied**\n"

        for region, resources in config.MAINTENANCE.items():
            msg += f"**{region}**\n"
            for resource, amount in resources.items():

                database.change_resource(region, resource, -amount)
                msg += f"{amount} {resource}\n"
            msg += "--------------------------\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)
        if log:
            await log.send(msg+ "\n=======================\n")

        # send debuffs as separate messages
        for region in config.MAINTENANCE.keys():
            debuffs = calculate_debuffs(region)

            if not debuffs:
                continue

            msg_debuff = f"⚠ **{region} Debuffs**\n"
            for d in debuffs.values():
                msg_debuff += f"```diff\n- {d['name']} (Tier {d['tier']})```\n"

            await log.send(msg_debuff)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Maintenance cancelled.",
            view=None
        )

@tasks.loop(hours=168)
async def weekly_maintenance():

    guild = bot.guilds[0]
    log = await log_channel(guild)

    msg = "**Weekly Maintenance Applied**\n"

    for region, resources in config.MAINTENANCE.items():

        for resource, amount in resources.items():

            database.change_resource(region, resource, -amount)

            msg += f"{region}: -{amount} {resource}\n"

    if log:
        await log.send(msg + "\n=======================\n")

@staff.command(name="maintenance", description="Apply maintenance costs")

async def maintenance(interaction: discord.Interaction):

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    msg = "**Confirm Maintenance Cycle**\n\n"

    for region, resources in config.MAINTENANCE.items():

        for resource, amount in resources.items():
            msg += f"{region}: -{amount} {resource}\n"

    await interaction.response.send_message(
        msg,
        view=MaintenanceConfirm(),
        ephemeral=True
    )
# -------------------------------
# Run
# -------------------------------
if __name__ == '__main__':
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        if not TOKEN:
            print("Please set DISCORD_TOKEN in your environment or .env file.")
            exit(1)
    else:
        bot.run(TOKEN)