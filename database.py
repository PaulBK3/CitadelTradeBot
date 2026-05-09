import sqlite3
import config

conn = sqlite3.connect("economy.db")
cursor = conn.cursor()

def setup():

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stockpiles (
        region TEXT,
        resource TEXT,
        amount INTEGER,
        PRIMARY KEY(region,resource)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        resource TEXT,
        amount INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS buffs (
        region TEXT,
        buff_type TEXT,
        tier TEXT,
        PRIMARY KEY(region, buff_type)
    )
    """)

    conn.commit()

def get_stockpile(region):

    cursor.execute("SELECT resource,amount FROM stockpiles WHERE region=?", (region,))
    rows = cursor.fetchall()

    return {r:a for r,a in rows}

def change_resource(region, resource, amount):

    cursor.execute("""
    INSERT INTO stockpiles(region,resource,amount)
    VALUES(?,?,?)
    ON CONFLICT(region,resource)
    DO UPDATE SET amount = stockpiles.amount + excluded.amount
    """,(region,resource,amount))

    conn.commit()

def get_amount(region,resource):

    cursor.execute(
        "SELECT amount FROM stockpiles WHERE region=? AND resource=?",
        (region,resource)
    )

    result = cursor.fetchone()

    return result[0] if result else 0

def transfer_stockpile(sender, receiver):

    cursor.execute(
        "SELECT resource, amount FROM stockpiles WHERE region=?",
        (sender,)
    )

    rows = cursor.fetchall()

    for resource, amount in rows:

        # remove from sender
        change_resource(sender, resource, -amount)

        # add to receiver
        change_resource(receiver, resource, amount)

    conn.commit()

def log_trade(sender,receiver,resource,amount):

    cursor.execute(
        "INSERT INTO trades(sender,receiver,resource,amount) VALUES(?,?,?,?)",
        (sender,receiver,resource,amount)
    )

    conn.commit()

    return cursor.lastrowid

def get_buff(region, buff_type):

    cursor.execute("SELECT tier FROM buffs WHERE region=? AND buff_type=?", (region, buff_type))

    result = cursor.fetchone()

    return result[0] if result else None

def set_buff(region, buff_type, tier):

    cursor.execute("""
    INSERT INTO buffs(region, buff_type, tier)
    VALUES(?,?,?)
    ON CONFLICT(region, buff_type)
    DO UPDATE SET tier = excluded.tier
    """, (region, buff_type, tier))

    conn.commit()

def set_amount(region, resource, amount):
    cursor.execute("""
    INSERT INTO stockpiles(region, resource, amount)
    VALUES(?, ?, ?)
    ON CONFLICT(region, resource)
    DO UPDATE SET amount = excluded.amount
    """, (region, resource, amount))
    conn.commit()

def get_last_transfers(region, limit=10):
    cursor.execute("""
    SELECT id, sender, receiver, resource, amount, timestamp
    FROM trades
    WHERE sender=? OR receiver=?
    ORDER BY timestamp DESC
    LIMIT ?
    """, (region, region, limit))
    
    return cursor.fetchall()