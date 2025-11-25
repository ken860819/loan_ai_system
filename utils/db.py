import sqlite3
import os
from datetime import datetime

DB_PATH = "db/loan.db"

# ===========================================
# 连接資料庫
# ===========================================
def get_conn():
    os.makedirs("db", exist_ok=True)
    return sqlite3.connect(DB_PATH)


# ===========================================
# 自動生成 user_id
# 姓名 + 流水號 + 身分證後四碼
# ===========================================
def generate_user_id(name: str, id_last4: str):
    """Ex: 王小明 + 00012 + 1234 → 王小明_00012_1234"""
    conn = get_conn()
    cur = conn.cursor()

    # 找目前幾筆（決定流水號）
    cur.execute("SELECT COUNT(*) FROM accounts")
    count = cur.fetchone()[0] + 1

    serial = str(count).zfill(5)  # 00001, 00002...

    user_id = f"{name}_{serial}_{id_last4}"

    conn.close()
    return user_id


# ===========================================
# 新增帳戶（第一次建立）
# ===========================================
def add_account(user_id, name, pd, limit_amount):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO accounts (user_id, name, pd, limit_amount, available_credit, outstanding_balance)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, name, pd, limit_amount, limit_amount, 0))

    conn.commit()
    conn.close()


# ===========================================
# 查詢帳戶資料
# ===========================================
def get_account(user_id):
    conn = get_conn()
    cur = conn.cursor()
    row = cur.execute(
        "SELECT user_id, name, pd, limit_amount, available_credit, outstanding_balance FROM accounts WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    # 把 tuple → dict
    return {
        "user_id": row[0],
        "name": row[1],
        "pd": row[2],
        "limit_amount": row[3],
        "available_credit": row[4],
        "outstanding_balance": row[5],
    }


# ===========================================
# 借款
# ===========================================
def borrow(user_id, amount):
    conn = get_conn()
    cur = conn.cursor()

    # 更新可用額度與餘額
    cur.execute("""
        UPDATE accounts
        SET available_credit = available_credit - ?,
            outstanding_balance = outstanding_balance + ?
        WHERE user_id=?
    """, (amount, amount, user_id))

    # 記錄交易
    cur.execute("""
        INSERT INTO transactions (user_id, type, amount, timestamp)
        VALUES (?, 'borrow', ?, ?)
    """, (user_id, amount, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ===========================================
# 還款
# ===========================================
def repay(user_id, amount):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE accounts
        SET available_credit = available_credit + ?,
            outstanding_balance = outstanding_balance - ?
        WHERE user_id=?
    """, (amount, amount, user_id))

    cur.execute("""
        INSERT INTO transactions (user_id, type, amount, timestamp)
        VALUES (?, 'repay', ?, ?)
    """, (user_id, amount, datetime.now().isoformat()))

    conn.commit()
    conn.close()


# ===========================================
# 查詢帳戶所有交易
# ===========================================
def list_transactions(user_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT type, amount, timestamp
        FROM transactions
        WHERE user_id=?
        ORDER BY timestamp DESC
    """, (user_id,))
    
    rows = cur.fetchall()
    conn.close()
    return rows
