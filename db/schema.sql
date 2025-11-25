-- 帳戶資料表：每個用戶一筆
CREATE TABLE IF NOT EXISTS accounts (
    user_id TEXT PRIMARY KEY,           -- 姓名 + 流水號 + 身分證後四碼
    name TEXT,
    pd REAL,                             -- AI 評估 PD
    limit_amount REAL,                   -- 總額度（核准額度）
    available_credit REAL,               -- 可用額度（會因借款／還款改變）
    outstanding_balance REAL             -- 未償還餘額（隨借隨還）
);

-- 交易紀錄：借款 / 還款 都記錄
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    type TEXT,                           -- borrow / repay
    amount REAL,
    timestamp TEXT
);
