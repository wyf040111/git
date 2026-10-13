# -*- coding: utf-8 -*-
"""
第 2 课：SQLite 真数据库 + 查询余额 + 充值
============================
相比第 1 课的升级：
1. 数据从"内存字典" → 存到真实数据库文件 shop.db（重启不丢）
2. 新增"充值"接口，真正修改数据
"""

import sqlite3
from flask import Flask, request, jsonify

# ---------- 0) 数据库连接 ----------
DB_FILE = "shop.db"   # 数据就存在这个文件里

def get_db():
    """开一条连接通道，用完记得关。row_factory让查询结果能按列名取。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- 1) 建表 + 插入初始客户 ----------
def init_db():
    conn = get_db()
    # 建表：users 表，id/姓名/余额
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id      INTEGER PRIMARY KEY,
            name    TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0
        )
    """)
    # 如果表是空的，放入 3 个初始客户
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        conn.executemany(
            "INSERT INTO users (id, name, balance) VALUES (?, ?, ?)",
            [
                (1001, "小王", 10.00),
                (1002, "小李", 22.87),
                (1003, "小张", 55.50),
            ]
        )
    conn.commit()
    conn.close()

init_db()  # 程序一启动就确保数据库就绪

app = Flask(__name__)

# ---------- 2) 查询余额（从数据库读） ----------
@app.route("/balance", methods=["GET"])
def get_balance():
    user_id = request.args.get("user_id")
    if user_id is None:
        return jsonify({"error": "缺少参数 user_id，示例：/balance?user_id=1001"}), 400

    conn = get_db()
    row = conn.execute(
        "SELECT id, name, balance FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()
    conn.close()

    if row:
        return jsonify({
            "user_id": row["id"],
            "name": row["name"],
            "balance": row["balance"],
            "message": "查询成功",
        })
    return jsonify({"error": "查无此用户"}), 404

# ---------- 3) 充值（往数据库里改钱） ----------
@app.route("/recharge", methods=["POST"])
def recharge():
    # 充值要"带数据来"，所以用 POST。数据以 JSON 放在请求体里
    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    amount = data.get("amount")

    if user_id is None or amount is None:
        return jsonify({"error": "请提供 user_id 和 amount，例如：{\"user_id\":1001,\"amount\":50}"}), 400

    conn = get_db()
    row = conn.execute(
        "SELECT id, balance FROM users WHERE id = ?", (int(user_id),)
    ).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "查无此用户"}), 404

    new_balance = row["balance"] + amount
    conn.execute(
        "UPDATE users SET balance = ? WHERE id = ?", (new_balance, int(user_id))
    )
    conn.commit()
    conn.close()

    return jsonify({
        "user_id": user_id,
        "balance": new_balance,
        "message": "充值成功",
    })

# ---------- 4) 首页 ----------
@app.route("/", methods=["GET"])
def home():
    return "欢迎！接口：/balance?user_id=1001 查余额；/recharge 充值（POST，body传JSON）"

# ---------- 5) 启动 ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)