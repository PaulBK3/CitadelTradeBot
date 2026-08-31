from importlib import resources

import discord
from discord import app_commands
from discord.ext import commands, tasks
import config
import os
import database
import math

from dotenv import load_dotenv


load_dotenv()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

database.setup()

async def region_autocomplete(
    interaction: discord.Interaction,
    current: str
):

    regions = database.get_regions()

    current = current.lower()

    return [
        app_commands.Choice(
            name=region,
            value=region
        )
        for region in regions
        if current in region.lower()
    ][:25]

async def duchy_autocomplete(
    interaction: discord.Interaction,
    current: str
):
    duchies = database.get_duchies()

    current = current.lower()

    return [
        app_commands.Choice(
            name=name,
            value=name
        )
        for name, region, withholding in duchies
        if current in name.lower()
    ][:25]

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

    regions = [r.name for r in member.roles if r.name in database.get_regions()]

    if len(regions) == 1:
        return regions[0]
    #handle dragonstaone/crownlands dual role and pentos/lys/braavos dual roles
    if len(regions)== 2:
        if "Dragonstone" in regions:
            return regions[0] if regions[1] == "Crownlands" else regions[1]
        if "Pentos" in regions:
            return regions[1] if regions[1] == "Pentos" else regions[0]
        if "Lys" in regions:
            return regions[1] if regions[1] == "Lys" else regions[0]
        if "Braavos" in regions:
            return regions[1] if regions[1] == "Braavos" else regions[0]
        if "Triarchy" in regions:
            return regions[1] if regions[1] == "Triarchy" else regions[0]
    return None

async def log_channel(guild):

    for channel in guild.text_channels:
        if channel.name == config.TRADE_LOG_CHANNEL:
            return channel

async def save_edit_channel(guild):
    for channel in guild.text_channels:
        if channel.name == config.SAVE_EDIT_CHANNEL:
            return channel
'''
def build_ck3_commands(msg: str, type: str, modifier_name: str, tier: int):
    if type == "county":
        msg += f"\neffect this = {{ every_held_title = {{ limit = {{ is_county = yes }} add_county_modifier = {{ modifier = {modifier_name}{tier} years = 10 }} }} }}\n"
        msg += f"\neffect this = {{ every_vassal_or_below = {{ limit = {{ is_landed = yes }} every_held_title = {{ limit = {{ is_county = yes }} add_county_modifier = {{ modifier = {modifier_name}{tier} years = 10 }} }} }} }}"
    if type == "character":
        msg += f"\neffect this = {{ add_character_modifier = {{ modifier = {modifier_name}{tier} years = 10 }} every_vassal_or_below = {{ add_character_modifier = {{ modifier = {modifier_name}{tier} years = 10 }} }} }}"
    if type == "midweek":
        return msg
    return msg
'''
def calculate_buff_cost(region, buff_type, tier):
    buff_data = config.BUFFS[buff_type]

    tier_name = list(buff_data["tiers"].keys())[tier - 1]

    base_cost = buff_data["tiers"][tier_name]["cost"]

    duchy_count = database.get_contributing_duchy_count(region)

    return {
        resource: amount * duchy_count
        for resource, amount in base_cost.items()
    }

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
# traders setup
# -------------------

@staff.command(
    name="assign_trader",
    description="Assign a Discord user as the trader for a region"
)
@app_commands.describe(
    region="Region the trader represents",
    user="Discord user who will be the trader"
)
@app_commands.autocomplete(
    region=region_autocomplete
)
async def assign_trader(
    interaction: discord.Interaction,
    region: str,
    user: discord.Member
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    old_user_id = database.get_regional_trader(region)

    database.set_regional_trader(
        region,
        user.id
    )

    if old_user_id:
        old_user = interaction.guild.get_member(old_user_id)

        if old_user:
            old_name = old_user.mention
        else:
            old_name = f"<@{old_user_id}>"

        message = (
            f"{region}'s trader has been changed.\n"
            f"Previous trader: {old_name}\n"
            f"New trader: {user.mention}"
        )

    else:
        message = (
            f"{user.mention} is now the trader for **{region}**."
        )

    await interaction.response.send_message(
        message,
        ephemeral=True
    )

@staff.command(
    name="remove_trader",
    description="Remove the trader assigned to a region"
)
@app_commands.describe(
    region="Region whose trader should be removed"
)
@app_commands.autocomplete(
    region=region_autocomplete
)
async def remove_trader(
    interaction: discord.Interaction,
    region: str
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    trader_id = database.get_regional_trader(region)

    if trader_id is None:
        await interaction.response.send_message(
            f"{region} does not currently have a trader.",
            ephemeral=True
        )
        return

    database.remove_regional_trader(region)

    await interaction.response.send_message(
        f"Removed the trader for **{region}**.",
        ephemeral=True
    )

@staff.command(
    name="traders",
    description="View the trader assigned to each region"
)
async def traders(
    interaction: discord.Interaction
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    rows = database.get_all_regional_traders()

    if not rows:
        await interaction.response.send_message(
            "No regional traders have been assigned.",
            ephemeral=True
        )
        return

    msg = "**Regional Traders**\n\n"

    trader_map = dict(rows)

    for region in database.get_regions():

        user_id = trader_map.get(region)

        if user_id is None:
            msg += f"**{region}** — No trader assigned\n"
        else:
            member = interaction.guild.get_member(user_id)

            if member:
                msg += f"**{region}** — {member.mention}\n"
            else:
                msg += f"**{region}** — <@{user_id}>\n"

    await interaction.response.send_message(
        msg,
        ephemeral=True
    )

# -------------------
# STOCKPILE
# -------------------

#for player
@bot.tree.command(name="stockpile", description="View your region's stockpile")
async def stockpile(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE) and not has_role(interaction.user, config.GREAT_HOUSE_ROLE):
        await interaction.followup.send(
            "You need the Trade Charter or Great House role.",
            ephemeral=True
        )
        return

    region = database.get_trader_region(interaction.user.id)

    if region is None:
        await interaction.response.send_message(
            "You are not assigned as the trader for any region.",
            ephemeral=True
        )
        return

    sender = region

    data = database.get_stockpile(region)
    economy = database.get_region_economy(region)

    maintenance = {
        resource: values["maintenance"]
        for resource, values in economy.items()
    }

    production = {
        resource: values["production"]
        for resource, values in economy.items()
    }

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
    duchies = database.get_region_duchy_summary(region)

    msg += "\n**Duchies**\n"

    if not duchies:
        msg += "No duchies registered.\n"
    else:
        for name, withholding in duchies:
            if withholding:
                msg += f"✗ {name} — WITHHOLDING\n"
            else:
                msg += f"✓ {name}\n"

    print("STOCKPILE CALLED", region)

    await interaction.followup.send(msg, ephemeral=True)

#for staff

@staff.command(name="stockpile_region", description="View a specific region's stockpile")

@app_commands.describe(region="Region to inspect")

@app_commands.autocomplete(
    region=region_autocomplete
)

async def stockpile_region(interaction: discord.Interaction, region: str):

    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.followup.send(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if region not in database.get_regions():

        await interaction.followup.send(
            "Invalid region.",
            ephemeral=True
        )
        return

    data = database.get_stockpile(region)
    economy = database.get_region_economy(region)

    maintenance = {
        resource: values["maintenance"]
        for resource, values in economy.items()
    }

    production = {
        resource: values["production"]
        for resource, values in economy.items()
    }
    
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
    
    print("STOCKPILE_REGION CALLED", region)

    await interaction.followup.send(msg, ephemeral=True)

@staff.command(name="stockpile_all_regions", description="View all regions' stockpiles")

async def stockpile_all_regions(interaction: discord.Interaction):

    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.followup.send(
            "Trade Team only.",
            ephemeral=True
        )
        return
    for region in database.get_regions():

        data = database.get_stockpile(region)
        economy = database.get_region_economy(region)

        maintenance = {
            resource: values["maintenance"]
            for resource, values in economy.items()
        }

        production = {
            resource: values["production"]
            for resource, values in economy.items()
        }

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

        # Send each region separately
        await interaction.followup.send(msg, ephemeral=True)

# -------------------
# VIEW LAST TRANSFERS
# -------------------

@bot.tree.command(name="transactions", description="View the last transactions from and to your region")
async def transactions(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE) and not has_role(interaction.user, config.GREAT_HOUSE_ROLE):
        await interaction.followup.send(
            "You need the Trade Charter or Great House role.",
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

    transfers = database.get_last_transfers(region)

    if not transfers:
        await interaction.followup.send(
            f"No transactions found for {region}.",
            ephemeral=True
        )
        return

    msg = f"**{region} - Last Transactions**\n"
    msg += "```\n"
    msg += f"{'ID':<5}{'Direction':<12}{'Partner':<15}{'Resource':<12}{'Amount':<8}\n"
    msg += "-" * 55 + "\n"

    for trade_id, sender, receiver, resource, amount, timestamp in transfers:
        if sender == region:
            direction = "→ OUT"
            partner = receiver
        else:
            direction = "← IN"
            partner = sender
        
        msg += f"{trade_id:<5}{direction:<12}{partner:<15}{resource:<12}{amount:<8}\n"

    msg += "```"

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
            await log.send("Stockpile Transfer\n" + msg + "=======================\n")

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

@app_commands.autocomplete(
    sender=region_autocomplete,
    receiver=region_autocomplete
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
            #msg = build_ck3_commands(msg, config.BUFFS[self.buff_type]['type'], config.BUFFS[self.buff_type]['modifier_name'], self.tier)
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

    region = database.get_trader_region(interaction.user.id)
    
    cost = calculate_buff_cost(
        region,
        buff_type,
        tier
    )

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

    def __init__(self, sender, receiver, resource, amount, rp_link, rumor, escorts, comment=None):
        super().__init__(timeout=30)

        self.sender = sender
        self.receiver = receiver
        self.resource = resource
        self.amount = amount
        self.rp_link = rp_link
        self.rumor = rumor
        self.escorts = escorts
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
            f"RP Link: {self.rp_link}\n"
            f"Escorts: {self.escorts}\n"
            f"Rumor post: {self.rumor}"
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
    rumor="Link to rumor post",
    escorts="Troops/Fleets escorting the trade",
    comment="Optional note about the trade"
)
@app_commands.choices(
    resource=RESOURCE_CHOICES + [app_commands.Choice(name="Gold", value="Gold")]
)
@app_commands.autocomplete(
    receiver = region_autocomplete
)
async def trade(
    interaction: discord.Interaction,
    receiver: str,
    resource: str,
    amount: int,
    rp_link: str,
    rumor: str,
    escorts: str,
    comment: str | None = None
):

    if not has_role(interaction.user, config.TRADE_CHARTER_ROLE):

        await interaction.response.send_message(
            "You lack Trade CHARTA.",
            ephemeral=True
        )
        return

    region = database.get_trader_region(interaction.user.id)

    if region is None:
        await interaction.response.send_message(
            "You are not assigned as the trader for any region.",
            ephemeral=True
        )
        return

    sender = region

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
        if not rp_link.startswith("https://"):
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
        #check RP link format (basic check, can be improved)
    if rumor not  in ["", None]:
        if not rumor.startswith("https://"):
            await interaction.response.send_message(
                "Invalid rumor link format.",
                ephemeral=True
            )
            return
    else:
        await interaction.response.send_message(
            "No rumor link provided. Please include a link to the rumor post.",
            ephemeral=True
        )
        return
    
    view = TradeConfirm(sender, receiver, resource, amount, rp_link, rumor, escorts, comment)

    msg = (
        f"Confirm Trade\n\n"
        f"Sender: {sender}\n"
        f"Receiver: {receiver}\n"
        f"Resource: {resource}\n"
        f"Amount: {amount}\n"
        f"RP Link: {rp_link}"
        f"Rumor post: {rumor}\n"
        f"Escorts: {escorts}"
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
    resource=RESOURCE_CHOICES
)
@app_commands.autocomplete(
    region= region_autocomplete
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

    @discord.ui.button(
    label="Confirm Production",
    style=discord.ButtonStyle.green
)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        msg = "**Production Applied**\n"

        for region in database.get_regions():

            economy = database.get_region_economy(region)

            if not economy:
                continue

            msg += f"**{region}**\n"

            for resource, values in economy.items():

                amount = values["production"]

                if amount <= 0:
                    continue

                database.change_resource(
                    region,
                    resource,
                    amount
                )

                msg += f"+{amount} {resource}\n"

            msg += "--------------------------\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)

        if log:
            await log.send(
                msg + "\n=======================\n"
            )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Production cancelled.",
            view=None
        )

@staff.command(name="production", description="Apply weekly production")

async def production(interaction: discord.Interaction):

    if not has_role(interaction.user, config.TRADE_TEAM_ROLE):

        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    msg = "**Confirm Production Cycle**\n\n"

    for region in database.get_regions():
    
                economy = database.get_region_economy(region)
    
                if not economy:
                    continue

                for resource, values in economy.items():
                    amount = values["production"]
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

    duchy_count = database.get_contributing_duchy_count(region)

    if duchy_count <= 0:
        return debuffs

    for resource, data in config.DEBUFFS.items():

        amount = database.get_amount(
            region,
            resource
        )

        if amount >= 0:
            continue

        deficit = abs(amount)

        tier = math.ceil(
            deficit / duchy_count
        )

        tier = min(tier, 3)

        debuffs[resource] = {
            "tier": tier,
            "name": data["tiers"][tier]["name"],
            "type": data["type"],
            "modifier_name": data["modifier_name"]
        }

        # Reset the negative stockpile after applying
        # the debuff.
        database.set_amount(
            region,
            resource,
            0
        )

    return debuffs

class MaintenanceConfirm(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(
    label="Confirm Maintenance",
    style=discord.ButtonStyle.green
)
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        msg = "**Maintenance Applied**\n"

        for region in database.get_regions():

            economy = database.get_region_economy(region)

            if not economy:
                continue

            msg += f"**{region}**\n"

            for resource, values in economy.items():

                amount = values["maintenance"]

                if amount <= 0:
                    continue

                database.change_resource(
                    region,
                    resource,
                    -amount
                )

                msg += f"-{amount} {resource}\n"

            msg += "--------------------------\n"

        await interaction.response.edit_message(
            content=msg,
            view=None
        )

        log = await log_channel(interaction.guild)

        if log:
            await log.send(
                msg + "\n=======================\n"
            )

        for region in database.get_regions():

            debuffs = calculate_debuffs(region)

            if not debuffs or not log:
                continue

            msg_debuff_region = f"⚠ **{region} Debuffs**\n"
            msg_debuff = ""

            for d in debuffs.values():

                msg_debuff += (
                    f"- {d['name']} "
                    f"(Tier {d['tier']})"
                )
                '''
                msg_debuff = build_ck3_commands(
                    msg_debuff,
                    d["type"],
                    d["modifier_name"],
                    d["tier"]
                )'''

                msg_debuff += "\n\n"

            await log.send(
                msg_debuff_region +
                "```diff\n" +
                msg_debuff +
                "```\n"
            )

        withholding = database.get_withholding_duchy_resources()

        if withholding:

            msg_withholding = "\n**Withholding Duchies**\n"

            current_duchy = None

            for duchy, region, resource, amount in withholding:

                if duchy != current_duchy:

                    msg_withholding += f"\n**{duchy}** ({region})\n"
                    current_duchy = duchy

                msg_withholding += f"{resource}: {amount}\n"

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.edit_message(
            content="Maintenance cancelled.",
            view=None
        )

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
# Duchy commands
# -------------------------------
@staff.command(name="create_duchy",description="Create a duchy")

@app_commands.describe(name="Name of the duchy", region="Region the duchy belongs to")
@app_commands.autocomplete(
    region=region_autocomplete
)
async def create_duchy(
    interaction: discord.Interaction,
    name: str,
    region: str
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if database.duchy_exists(name):
        await interaction.response.send_message(
            "That duchy already exists.",
            ephemeral=True
        )
        return

    database.create_duchy(name, region)

    await interaction.response.send_message(
        f"Created **{name}** in **{region}**.",
        ephemeral=True
    )

@staff.command(
    name="assign_duchy",
    description="Move a duchy to another region"
)
@app_commands.describe(
    duchy="Duchy to move",
    region="New region"
)
@app_commands.autocomplete(
    duchy=duchy_autocomplete,
    region=region_autocomplete
)
async def assign_duchy(
    interaction: discord.Interaction,
    duchy: str,
    region: str
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    old = database.get_duchy(duchy)

    if not old:
        await interaction.response.send_message(
            "Unknown duchy.",
            ephemeral=True
        )
        return

    old_region = old[1]

    database.assign_duchy(
        duchy,
        region
    )

    await interaction.response.send_message(
        f"**{duchy}** moved from "
        f"**{old_region}** to **{region}**.",
        ephemeral=True
    )

@staff.command(
    name="set_duchy_withholding",
    description="Toggle whether a duchy contributes to its region"
)
@app_commands.describe(
    duchy="Duchy",
    withholding="Whether the duchy withholds its resources"
)
@app_commands.autocomplete(
    duchy=duchy_autocomplete
)
async def set_duchy_withholding(
    interaction: discord.Interaction,
    duchy: str,
    withholding: bool
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if not database.duchy_exists(duchy):
        await interaction.response.send_message(
            "Unknown duchy.",
            ephemeral=True
        )
        return

    database.set_duchy_withholding(
        duchy,
        withholding
    )

    region = database.get_duchy_region(
        duchy
    )

    if withholding:
        status = "WITHHOLDING"
    else:
        status = "CONTRIBUTING"

    await interaction.response.send_message(
        f"**{duchy}** in **{region}** is now "
        f"**{status}**.",
        ephemeral=True
    )

@staff.command(
    name="duchies",
    description="View duchies and their economic status"
)
@app_commands.describe(
    region="Optional region to inspect"
)
@app_commands.autocomplete(
    region=region_autocomplete
)
async def duchies(
    interaction: discord.Interaction,
    region: str | None = None
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if region:
        regions = [region]
    else:
        regions = database.get_regions()

    msg = "**Duchy Economic Status**\n\n"

    for current_region in regions:

        rows = database.get_region_duchy_summary(
            current_region
        )

        if not rows:
            continue

        msg += f"**{current_region}**\n"

        for name, withholding in rows:

            if withholding:
                msg += f"✗ {name} — WITHHOLDING\n"
            else:
                msg += f"✓ {name} — contributing\n"

        msg += "\n"

    await interaction.response.send_message(
        msg,
        ephemeral=True
    )

@staff.command(
    name="create_region",
    description="Create a new kingdom/region"
)
@app_commands.describe(
    name="Name of the kingdom"
)
async def create_region(
    interaction: discord.Interaction,
    name: str
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if database.region_exists(name):
        await interaction.response.send_message(
            "That kingdom already exists.",
            ephemeral=True
        )
        return

    database.create_region(name)

    await interaction.response.send_message(
        f"Created **{name}**.",
        ephemeral=True
    )

class DeleteRegionConfirm(discord.ui.View):

    def __init__(self, region):
        super().__init__(timeout=60)
        self.region = region

    @discord.ui.button(
        label="Confirm Delete",
        style=discord.ButtonStyle.danger
    )
    async def confirm(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        region = self.region

        # Do not allow deletion while duchies still belong
        # to the region.
        duchies = database.get_duchies(region)

        if duchies:
            names = ", ".join(
                duchy[0]
                for duchy in duchies
            )

            await interaction.response.edit_message(
                content=(
                    f"Cannot delete **{region}**.\n\n"
                    f"The following duchies are still assigned to it:\n"
                    f"{names}\n\n"
                    f"Move all duchies to another region first."
                ),
                view=None
            )
            return

        if not database.region_exists(region):
            await interaction.response.edit_message(
                content=(
                    f"**{region}** no longer exists."
                ),
                view=None
            )
            return

        # Remove the region's trader assignment.
        database.remove_regional_trader(region)

        # Remove regional buffs.
        #database.delete_region_buffs(region)

        # Remove regional stockpile.
        #database.delete_region_stockpile(region)

        # Finally remove the region itself.
        database.delete_region(region)

        await interaction.response.edit_message(
            content=f"Deleted **{region}**.",
            view=None
        )

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="Region deletion cancelled.",
            view=None
        )

@staff.command(
    name="delete_region",
    description="Remove a kingdom/region"
)
@app_commands.describe(
    region="Kingdom to remove"
)
@app_commands.autocomplete(
    region=region_autocomplete
)
async def delete_region(
    interaction: discord.Interaction,
    region: str
):

    if not has_role(
        interaction.user,
        config.TRADE_TEAM_ROLE
    ):
        await interaction.response.send_message(
            "Trade Team only.",
            ephemeral=True
        )
        return

    if not database.region_exists(region):
        await interaction.response.send_message(
            "That kingdom does not exist.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Delete **{region}**?\n"
        f"This should only be done after moving its duchies "
        f"and handling its stockpile/trades.",
        view=DeleteRegionConfirm(region),
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