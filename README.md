# Discord Trade Bot

A configurable **Discord economy and trade bot** designed for Citadel roleplay server.

The bot manages **regional stockpiles, trade between regions, weekly production, and maintenance costs**, with all economic configuration stored in a single file for easy balancing.

---

# Features

### Regional Economy

* Track stockpiles for multiple regions
* Multiple resource types
* Persistent storage using SQLite

### Slash Commands

* `/stockpile` — View the stockpile of your own region (Trade Charta only)
* `/stockpile_region` — View the stockpile of any region (Trade Team only)
* `/trade` — Send resources to another region
* `/buy_buff` — Purchase buffs for regions (Trade Team only)
* `/modstock` — Modify stockpiles (trade team only)
* `/production` — Apply weekly production
* `/maintenance` — Apply weekly maintenance costs

Most command responses are ephemeral (only visible to the user).
Trades and economy changes are logged in the configured trade log channel.
### Trade System

* Trade confirmation buttons
* Automatic resource validation
* Trade IDs for logging
* Logged transactions in a trade log channel

### Buff System

* Purchase buff tiers for regions using resources
* Buffs provide in-game advantages (tracked in database)
* Confirmation required for purchases
* Logged in trade log channel

### Automated Economy

* Optional Weekly production cycles
* Optional weekly maintenance cycles
* Config-driven economy balancing

### Role-Based Permissions

* **Trade Charta** role required for trading
* **Trade Team** role required for administrative actions
* **Region** determined from user roles

---

# Example Use Case

A player representing the **Vale** wants to send wood to the **Riverlands**.

```
/trade receiver:Riverlands resource:Wood amount:5
```

The bot prompts a **confirmation button** before executing the trade.

Once confirmed:

* Resources are deducted from the sender
* Resources are added to the receiver
* A log entry is created in the trade log channel

---

# Project Structure

```
tradebot/
│
├─ bot.py          # Main bot logic
├─ config.py       # Economy and role configuration
├─ database.py     # SQLite database logic
└─ economy.db      # Generated automatically
```

---

# Configuration

All economy settings are managed in **config.py**.

---

# Database

The bot uses **SQLite** for persistent storage.

Two tables are used:

### Stockpiles

```
region | resource | amount
```

### Trades

```
id | sender | receiver | resource | amount | timestamp
```

Each completed trade receives a **unique trade ID** for logging and auditing.

---

Permissions
Command	Required Role
/stockpile	Everyone
/trade	Trade Charta
/modstock	Trade Team
/production	Trade Team
/maintenance	Trade Team
Running the Bot


# Installation

## 1. Clone the Repository

```
git clone
cd tradebot
```

## 2. Install Dependencies

Requires Python 3.9+

```
pip install *packages*
```

This bot is built using **discord.py 2.x**, which supports Discord slash commands and UI buttons.

---
Create a Discord bot application in the Discord Developer Portal

Copy the bot token

Paste it into .env

TOKEN = "YOUR_BOT_TOKEN"

Run the bot:

python trader.py
