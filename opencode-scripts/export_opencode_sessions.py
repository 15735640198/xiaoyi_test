#!/usr/bin/env python3
"""
opencode session 导出工具
从 opencode.db 导出 session/message 数据为 jsonl 格式

用法:
  python3 export_opencode_sessions.py              # 导出所有 session
  python3 export_opencode_sessions.py -o ./out     # 指定输出目录
  python3 export_opencode_sessions.py -l           # 仅列出 session 不导出
"""
import sqlite3
import json
import shutil
import tempfile
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

DEFAULT_DB = Path.home() / ".local" / "share" / "opencode" / "opencode.db"
DEFAULT_OUT = Path.home() / ".local" / "share" / "opencode" / "export"


def open_db(db_path):
    """打开数据库,如果被锁则复制副本再读"""
    # 先试只读模式
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro&immutable=1", uri=True)
        conn.execute("SELECT count(*) FROM session").fetchone()
        return conn, None
    except Exception:
        pass

    # 数据库被锁,复制到临时目录
    tmp_dir = Path(tempfile.mkdtemp(prefix="opencode_db_"))
    for suffix in ["", "-wal", "-shm"]:
        src = Path(str(db_path) + suffix)
        dst = tmp_dir / f"opencode.db{suffix}"
        if src.exists():
            shutil.copy2(src, dst)

    conn = sqlite3.connect(str(tmp_dir / "opencode.db"))
    return conn, tmp_dir


def list_sessions(cur):
    """获取所有 session 列表"""
    cur.execute("""
        SELECT id, slug, title, directory, model, agent,
               tokens_input, tokens_output, tokens_reasoning,
               tokens_cache_read, tokens_cache_write, cost,
               time_created, time_updated
        FROM session
        ORDER BY time_created DESC
    """)
    return cur.fetchall()


def export_one_session(conn, sess, out_dir):
    """导出单个 session 为 jsonl 文件"""
    cur = conn.cursor()
    session_id = sess["id"]
    slug = sess["slug"] or "untitled"
    title = sess["title"] or "Untitled"
    ts = datetime.fromtimestamp(sess["time_created"] / 1000).strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_{slug}.jsonl"
    filepath = out_dir / filename

    # session 元信息行
    session_meta = {
        "type": "session",
        "session_id": session_id,
        "slug": slug,
        "title": title,
        "directory": sess["directory"],
        "agent": sess["agent"],
        "model": json.loads(sess["model"]) if sess["model"] else None,
        "tokens": {
            "input": sess["tokens_input"],
            "output": sess["tokens_output"],
            "reasoning": sess["tokens_reasoning"],
            "cache_read": sess["tokens_cache_read"],
            "cache_write": sess["tokens_cache_write"],
        },
        "cost": sess["cost"],
        "time_created": sess["time_created"],
        "time_updated": sess["time_updated"],
    }

    # 获取该 session 所有消息
    cur.execute("""
        SELECT id, session_id, time_created, time_updated, data
        FROM message
        WHERE session_id = ?
        ORDER BY time_created ASC
    """, (session_id,))
    messages = cur.fetchall()

    lines = [json.dumps(session_meta, ensure_ascii=False)]
    msg_count = 0

    for msg in messages:
        msg_data = json.loads(msg["data"]) if msg["data"] else {}

        # 获取该消息的内容片段(parts)
        cur.execute("""
            SELECT data FROM part
            WHERE message_id = ?
            ORDER BY time_created ASC
        """, (msg["id"],))
        parts = [json.loads(r["data"]) if r["data"] else {} for r in cur.fetchall()]

        record = {
            "type": "message",
            "message_id": msg["id"],
            "role": msg_data.get("role"),
            "model": msg_data.get("model"),
            "agent": msg_data.get("agent"),
            "parts": parts,
            "time_created": msg["time_created"],
            "time_updated": msg["time_updated"],
        }
        lines.append(json.dumps(record, ensure_ascii=False))
        msg_count += 1

    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return filename, msg_count


def main():
    parser = argparse.ArgumentParser(description="opencode session 导出工具")
    parser.add_argument("-d", "--db", default=str(DEFAULT_DB), help="opencode.db 路径")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUT), help="输出目录")
    parser.add_argument("-l", "--list", action="store_true", help="仅列出 session,不导出")
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.output)

    print("opencode Session 导出工具")
    print(f"  数据库: {db_path}")
    print(f"  输出目录: {out_dir}")
    print()

    if not db_path.exists():
        print(f"错误: 数据库不存在: {db_path}")
        sys.exit(1)

    conn, tmp_dir = open_db(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sessions = list_sessions(cur)

    if not sessions:
        print("没有找到任何 session。")
        conn.close()
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    print(f"找到 {len(sessions)} 个 session:\n")
    print(f"{'#':>3}  {'时间':<20}  {'标题':<20}  {'消息':>4}  {'Token(入/出)':>12}")
    print("-" * 75)

    for i, sess in enumerate(sessions):
        ts = datetime.fromtimestamp(sess["time_created"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        title = (sess["title"] or "Untitled")[:20]
        cur.execute("SELECT count(*) FROM message WHERE session_id = ?", (sess["id"],))
        msg_cnt = cur.fetchone()[0]
        tokens = f"{sess['tokens_input']}/{sess['tokens_output']}"
        print(f"{i+1:>3}  {ts:<20}  {title:<20}  {msg_cnt:>4}  {tokens:>12}")

    if args.list:
        conn.close()
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        return

    print()
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"开始导出到: {out_dir}\n")

    for sess in sessions:
        filename, msg_count = export_one_session(conn, sess, out_dir)
        ts = datetime.fromtimestamp(sess["time_created"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {filename}  ({msg_count} 条消息, token: {sess['tokens_input']}/{sess['tokens_output']})")

    conn.close()
    if tmp_dir:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n导出完成,共 {len(sessions)} 个 session。")


if __name__ == "__main__":
    main()
