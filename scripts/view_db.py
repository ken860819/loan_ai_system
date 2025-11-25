import sqlite3
import pandas as pd

DB_PATH = "db/loan.db"

conn = sqlite3.connect(DB_PATH)

# 列出所有 table
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("\n=== 資料庫內的 Tables ===")
print(tables)

print("\n=== accounts Table ===")
try:
    df_accounts = pd.read_sql("SELECT * FROM accounts", conn)
    print(df_accounts)
except Exception as e:
    print("accounts table error:", e)

print("\n=== transactions Table ===")
try:
    df_tx = pd.read_sql("SELECT * FROM transactions", conn)
    print(df_tx)
except Exception as e:
    print("transactions table error:", e)

conn.close()
