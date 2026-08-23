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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duchies (
        name TEXT PRIMARY KEY,
        region TEXT NOT NULL,
        withholding INTEGER NOT NULL DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS duchy_resources (
    duchy TEXT,
    resource TEXT,
    production INTEGER NOT NULL DEFAULT 0,
    maintenance INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(duchy, resource),
    FOREIGN KEY(duchy) REFERENCES duchies(name)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regional_traders (
        region TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regions (
        name TEXT PRIMARY KEY
    )
    """)
    conn.commit()

# -------------------
# Regions
# -------------------
def create_region(name):
    cursor.execute("""
        INSERT INTO regions(name)
        VALUES (?)
    """, (name,))

    conn.commit()

def region_exists(name):
    cursor.execute("""
        SELECT 1
        FROM regions
        WHERE name=?
    """, (name,))

    return cursor.fetchone() is not None

def delete_region(name):
    cursor.execute("""
        DELETE FROM regions
        WHERE name=?
    """, (name,))

    conn.commit()

def get_regions():
    cursor.execute("""
        SELECT name
        FROM regions
        ORDER BY name
    """)

    return [row[0] for row in cursor.fetchall()]

# -------------------
# REGIONAL TRADERS
# -------------------

def set_regional_trader(region, user_id):
    cursor.execute("""
        INSERT INTO regional_traders(region, user_id)
        VALUES (?, ?)
    """, (region, user_id))

    conn.commit()


def get_regional_trader(region):
    cursor.execute("""
        SELECT user_id
        FROM regional_traders
        WHERE region=?
    """, (region,))

    result = cursor.fetchone()

    return result[0] if result else None


def remove_regional_trader(user_id):
    cursor.execute("""
        DELETE FROM regional_traders
        WHERE user_id=?
    """, (user_id,))

    conn.commit()


def get_all_regional_traders():
    cursor.execute("""
        SELECT region, user_id
        FROM regional_traders
        ORDER BY region
    """)

    return cursor.fetchall()

def get_trader_region(user_id):
    cursor.execute("""
        SELECT region
        FROM regional_traders
        WHERE user_id=?
    """, (user_id,))

    result = cursor.fetchone()

    return result[0] if result else None


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

# -------------------
# DUCHIES
# -------------------

def create_duchy(name, region):
    cursor.execute("""
        INSERT INTO duchies(name, region, withholding)
        VALUES (?, ?, 0)
    """, (name, region))

    conn.commit()


def duchy_exists(name):
    cursor.execute(
        "SELECT 1 FROM duchies WHERE name=?",
        (name,)
    )

    return cursor.fetchone() is not None


def get_duchies(region=None):
    if region is None:
        cursor.execute("""
            SELECT name, region, withholding
            FROM duchies
            ORDER BY region, name
        """)
    else:
        cursor.execute("""
            SELECT name, region, withholding
            FROM duchies
            WHERE region=?
            ORDER BY name
        """, (region,))

    return cursor.fetchall()


def get_duchy(name):
    cursor.execute("""
        SELECT name, region, withholding
        FROM duchies
        WHERE name=?
    """, (name,))

    return cursor.fetchone()


def get_duchy_region(name):
    cursor.execute(
        "SELECT region FROM duchies WHERE name=?",
        (name,)
    )

    result = cursor.fetchone()

    return result[0] if result else None


def assign_duchy(name, region):
    cursor.execute("""
        UPDATE duchies
        SET region=?
        WHERE name=?
    """, (region, name))

    conn.commit()


def set_duchy_withholding(name, withholding):
    cursor.execute("""
        UPDATE duchies
        SET withholding=?
        WHERE name=?
    """, (1 if withholding else 0, name))

    conn.commit()


def is_duchy_withholding(name):
    cursor.execute("""
        SELECT withholding
        FROM duchies
        WHERE name=?
    """, (name,))

    result = cursor.fetchone()

    return bool(result[0]) if result else False

# -------------------
# DUCHY ECONOMY
# -------------------

def get_region_economy(region):
    cursor.execute("""
        SELECT
            dr.resource,
            COALESCE(SUM(dr.production), 0),
            COALESCE(SUM(dr.maintenance), 0)
        FROM duchy_resources dr
        JOIN duchies d
            ON d.name = dr.duchy
        WHERE d.region=?
          AND d.withholding=0
        GROUP BY dr.resource
    """, (region,))

    rows = cursor.fetchall()

    economy = {}

    for resource, production, maintenance in rows:
        economy[resource] = {
            "production": production,
            "maintenance": maintenance
        }

    return economy

def get_region_duchy_summary(region):
    cursor.execute("""
        SELECT
            name,
            withholding
        FROM duchies
        WHERE region=?
        ORDER BY name
    """, (region,))

    return cursor.fetchall()

def get_contributing_duchy_count(region):
    cursor.execute("""
        SELECT COUNT(*)
        FROM duchies
        WHERE region=?
          AND withholding=0
    """, (region,))

    result = cursor.fetchone()

    return result[0] if result else 0

def get_withholding_duchies():
    cursor.execute("""
        SELECT
            d.name,
            d.region,
            dr.resource,
            dr.production,
            dr.maintenance
        FROM duchies d
        LEFT JOIN duchy_resources dr
            ON dr.duchy = d.name
        WHERE d.withholding=1
        ORDER BY d.region, d.name, dr.resource
    """)

    return cursor.fetchall()

def get_withholding_duchy_resources():
    cursor.execute("""
        SELECT
            d.name,
            d.region,
            dr.resource,
            dr.amount
        FROM duchies d
        JOIN duchy_resources dr
            ON dr.duchy = d.name
        WHERE d.withholding=1
        ORDER BY d.region, d.name, dr.resource
    """)

    return cursor.fetchall()