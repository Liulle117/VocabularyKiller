# -*- coding: utf-8 -*-
"""ECDICT 离线词典查询。

只依赖标准库 sqlite3，运行时完全离线。
给定英文单词，返回：音标(IPA)、中文释义、英文释义。

词库文件（.db）放在本程序同目录下即可被自动识别。
"""
import glob
import os
import sqlite3
import sys

# 兼容 PyInstaller 打包：冻结后用 exe 所在目录
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME_CANDIDATES = ["ecdict.db", "stardict.db", "ecdict-sqlite.db", "ecdict.db"]


def find_db(explicit=None):
    """在项目目录中定位 ECDICT 的 SQLite 词库文件。"""
    if explicit and os.path.exists(explicit):
        return explicit
    for name in DB_NAME_CANDIDATES:
        p = os.path.join(BASE_DIR, name)
        if os.path.exists(p):
            return p
    # 退而求其次：递归找任意 .db，优先名字里带 dict 的
    dbs = glob.glob(os.path.join(BASE_DIR, "**", "*.db"), recursive=True)
    if dbs:
        dbs.sort(key=lambda p: (0 if "dict" in os.path.basename(p).lower() else 1, len(p)))
        return dbs[0]
    return None


class Dictionary:
    def __init__(self, db_path=None):
        self.db_path = find_db(db_path)
        self._conn = None
        self._table = None
        self._cols = set()
        self._error = None
        if not self.db_path:
            self._error = "未找到 ECDICT 词库文件（.db），请先把词库放到程序目录。"
            return
        try:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.text_factory = str
            self._detect_schema()
        except sqlite3.Error as e:  # pragma: no cover
            self._error = "打开词库失败：%s" % e
            self._conn = None

    def _detect_schema(self):
        cur = self._conn.cursor()
        tables = [r[0] for r in cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        for t in ("stardict", "ecdict", "dict", "words"):
            if t in tables:
                self._table = t
                break
        if not self._table and tables:
            self._table = tables[0]
        if self._table:
            info = cur.execute('PRAGMA table_info("%s")' % self._table).fetchall()
            self._cols = {row[1] for row in info}

    @property
    def available(self):
        return self._conn is not None and self._table is not None

    @property
    def error(self):
        return self._error

    @property
    def table(self):
        return self._table

    def lookup(self, word):
        """查询单词，返回 dict(word, phonetic, translation, definition)；查不到返回 None。"""
        if not self.available:
            return None
        w = (word or "").strip()
        if not w:
            return None
        cur = self._conn.cursor()
        want = [c for c in ("word", "phonetic", "translation", "definition") if c in self._cols]
        if not want:
            return None
        colstr = ",".join('"%s"' % c for c in want)
        row = None
        # ECDICT 用小写列 sw 做检索键，最快
        if "sw" in self._cols:
            row = cur.execute(
                'SELECT %s FROM "%s" WHERE sw=? LIMIT 1' % (colstr, self._table),
                (w.lower(),)).fetchone()
        if row is None and "word" in self._cols:
            row = cur.execute(
                'SELECT %s FROM "%s" WHERE word=? COLLATE NOCASE LIMIT 1' % (colstr, self._table),
                (w,)).fetchone()
        if row is None:
            return None
        d = dict(zip(want, row))
        phonetic = (d.get("phonetic") or "").strip()
        return {
            "word": (d.get("word") or w).strip(),
            "phonetic": phonetic,
            "translation": (d.get("translation") or "").strip(),
            "definition": (d.get("definition") or "").strip(),
        }

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None


def format_phonetic(p):
    """把音标包上斜杠（若尚无）。"""
    p = (p or "").strip()
    if not p:
        return ""
    if p.startswith("[") or p.startswith("/"):
        return p
    return "/%s/" % p
