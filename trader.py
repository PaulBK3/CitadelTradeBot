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

# -------------------
# Helpers
# -------------------

def has_role(member, role):

    return any(r.name == role for r in member.roles)


def get_region(member):

    regions = [r.name for r in member.roles if r.name in config.REGION_ROLES]

    if len(regions) == 1:
        return regions[0]

    return None


async def log_channel(guild):

    for channel in guild.text_channels:
        if channel.name == config.TRADE_LOG_CHANNEL:
            return channel
        
async def region_autocomplete(
    interaction: discord.Interaction,
    current: str
):

    return [
        app_commands.Choice(name=r, value=r)
        for r in config.REGION_ROLES
        if current.lower() in r.lower()
    ]
    
# -------------------
# Ready
# -------------------

@bot.event
async def on_ready():

    await bot.tree.sync()

    #weekly_production.start()
    #weekly_maintenance.start()

    print("Trade Bot Ready")

# -------------------
# STOCKPILE
# -------------------

#for player
@bot.tree.command(name="stockpile", description="View your region's stockpile")
async def stockpile(interaction: discord.Interaction):

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE):

        await interaction.response.send_message(
            "You need the Trade Charta role.",
            ephemeral=True
        )
        return

    region = get_region(interaction.user)

    if not region:

        await interaction.response.send_message(
            "No valid region role found.",
            ephemeral=True
        )
        return

    data = database.get_stockpile(region)

    msg = f"**{region} Stockpile**\n"

    for resource, amount in data.items():
        msg += f"{resource}: {amount}\n"

    await interaction.response.send_message(msg, ephemeral=True)

#for staff

@bot.tree.command(name="stockpile_region", description="View a specific region's stockpile")

@app_commands.describe(region="Region to inspect")

async def stockpile_region(interaction: discord.Interaction, region: str):

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if region not in config.REGION_ROLES:

        await interaction.response.send_message(
            "Invalid region.",
            ephemeral=True
        )
        return

    data = database.get_stockpile(region)

    msg = f"**{region} Stockpile**\n"

    for resource, amount in data.items():
        msg += f"{resource}: {amount}\n"

    await interaction.response.send_message(msg, ephemeral=True)

@stockpile_region.autocomplete("region")
async def stockpile_region_autocomplete(interaction, current):
    return await region_autocomplete(interaction, current)
# -------------------
# TRADE CONFIRMATION
# -------------------

class TradeConfirm(discord.ui.View):

    def __init__(self,sender,receiver,resource,amount):
        super().__init__(timeout=30)

        self.sender = sender
        self.receiver = receiver
        self.resource = resource
        self.amount = amount

    @discord.ui.button(label="Confirm Trade", style=discord.ButtonStyle.green)

    async def confirm(self,interaction:discord.Interaction,button:discord.ui.Button):

        database.change_resource(self.sender,self.resource,-self.amount)
        database.change_resource(self.receiver,self.resource,self.amount)

        trade_id = database.log_trade(
            self.sender,self.receiver,self.resource,self.amount
        )

        msg = (
            f"Trade #{trade_id}\n"
            f"{self.sender} ➜ {self.receiver}\n"
            f"{self.amount} {self.resource}"
        )

        await interaction.response.edit_message(content=msg,view=None)

        log = await log_channel(interaction.guild)
        await log.send(msg)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)

    async def cancel(self,interaction:discord.Interaction,button:discord.ui.Button):

        await interaction.response.edit_message(
            content="Trade cancelled.",
            view=None
        )

# -------------------
# TRADE COMMAND
# -------------------

@bot.tree.command(name="trade")

@app_commands.describe(
    receiver="Region receiving goods",
    resource="Resource type",
    amount="Amount"
)

async def trade(interaction:discord.Interaction,receiver:str,resource:str,amount:int):

    if not has_role(interaction.user,config.TRADE_CHARTER_ROLE):

        await interaction.response.send_message(
            "You lack Trade Charta.",
            ephemeral=True
        )

        return

    sender = get_region(interaction.user)

    if not sender:

        await interaction.response.send_message(
            "No region role found.",
            ephemeral=True
        )

        return

    current = database.get_amount(sender,resource)

    if receiver not in config.REGION_ROLES:

        await interaction.response.send_message(
            "Invalid region.",
            ephemeral=True
        )

        return

    if current < amount:

        await interaction.response.send_message(
            f"{sender} only has {current} {resource}",
            ephemeral=True
        )

        return

    view = TradeConfirm(sender,receiver,resource,amount)

    msg = (
        f"Confirm Trade\n\n"
        f"Sender: {sender}\n"
        f"Receiver: {receiver}\n"
        f"Resource: {resource}\n"
        f"Amount: {amount}"
    )

    await interaction.response.send_message(msg,view=view)

# -------------------
# MODIFY STOCKPILE
# -------------------

@bot.tree.command(name="modstock")

async def modstock(interaction:discord.Interaction,region:str,resource:str,amount:int):

    if not has_role(interaction.user,config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )

        return

    database.change_resource(region,resource,amount)

    msg = f"{region} {resource} {'+' if amount>=0 else ''}{amount}"

    await interaction.response.send_message(msg, ephemeral=True)

    log = await log_channel(interaction.guild)
    await log.send(f"MOD: {msg}")

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

            for resource, amount in resources.items():

                database.change_resource(region, resource, amount)
                msg += f"{region}: +{amount} {resource}\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)
        if log:
            await log.send(msg)

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
        await log.send(msg)

@bot.tree.command(name="production", description="Apply weekly production")

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
class MaintenanceConfirm(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="Confirm Maintenance", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):

        msg = "**Maintenance Applied**\n"

        for region, resources in config.MAINTENANCE.items():

            for resource, amount in resources.items():

                database.change_resource(region, resource, -amount)
                msg += f"{region}: -{amount} {resource}\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)
        if log:
            await log.send(msg)

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
        await log.send(msg)

@bot.tree.command(name="maintenance", description="Apply maintenance costs")

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