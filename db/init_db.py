import sqlite3, os

db_path = "db/loan.db"
schema_path = "db/schema.sql"

print("初始化資料庫...")

# 如果 loan.db 存在→刪掉重建（避免壞掉）
if os.path.exists(db_path):
    os.remove(db_path)
    print("舊的 loan.db 已刪除")

# 重新建立空 DB
conn = sqlite3.connect(db_path)

# 匯入 schema.sql（建立 accounts / transactions）
with open(schema_path, "r", encoding="utf-8") as f:
    conn.executescript(f.read())

conn.close()
print("資料庫建立完成！")
