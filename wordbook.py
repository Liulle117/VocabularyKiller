# -*- coding: utf-8 -*-
"""单词本持久化存储。

所有录入过的单词都保存在 wordbook.json 里，永久保留（这就是"单词本"）。
每个单词有一个 active 标记：
  - active=True  -> 属于"今日单词"（当前学习列表）
  - active=False -> 已归档，仍在单词本中，可随时复习

"清空今日单词"只是把所有 active 置为 False，不会删除任何单词，
因此第二天列表清零、但单词本完整保留。
"""
import json
import os
import sys
from collections import Counter
from datetime import date, datetime, timedelta

# 兼容 PyInstaller 打包：冻结后用 exe 所在目录
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "wordbook.json")


class WordBook:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self._data = {"version": 1, "words": {}}
        self.load()

    # ---------- 读写 ----------
    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict) and isinstance(loaded.get("words"), dict):
                    self._data = loaded
                else:
                    self._backup_corrupt()
            except (json.JSONDecodeError, OSError):
                self._backup_corrupt()
        self._data.setdefault("version", 1)
        self._data.setdefault("words", {})

    def _backup_corrupt(self):
        try:
            bad = self.path + ".corrupt"
            if os.path.exists(self.path):
                os.replace(self.path, bad)
        except OSError:
            pass
        self._data = {"version": 1, "words": {}}

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    # ---------- 数据 ----------
    @property
    def words(self):
        """dict: key=单词小写, value=单词记录。"""
        return self._data["words"]

    def count(self):
        return len(self._data["words"])

    def add(self, word, phonetic="", translation=""):
        """添加/更新一个单词，并标记为今日单词(active)。返回记录。"""
        word = (word or "").strip()
        if not word:
            return None
        key = word.lower()
        today = date.today().isoformat()
        existing = self.words.get(key)
        if existing:
            if phonetic:
                existing["phonetic"] = phonetic
            if translation:
                existing["translation"] = translation
            existing["active"] = True
            existing.setdefault("date_added", today)
            self.save()
            return existing
        rec = {
            "word": word,
            "phonetic": phonetic or "",
            "translation": translation or "",
            "date_added": today,
            "active": True,
            "review_count": 0,
            "correct_count": 0,
            "last_review": None,
        }
        self.words[key] = rec
        self.save()
        return rec

    def delete(self, word):
        key = (word or "").strip().lower()
        if key in self.words:
            del self.words[key]
            self.save()
            return True
        return False

    def get(self, word):
        return self.words.get((word or "").strip().lower())

    # ---------- 查询 ----------
    def all_words(self):
        """全部单词（按录入日期、再按单词排序）。"""
        return sorted(
            self.words.values(),
            key=lambda w: (w.get("date_added", ""), w.get("word", "").lower()),
        )

    def active_words(self):
        """今日单词（当前学习列表）。"""
        return [w for w in self.all_words() if w.get("active")]

    def words_by_date(self, d):
        return [w for w in self.all_words() if w.get("date_added") == d]

    def dates(self):
        """所有出现过的录入日期，倒序（最新在前）。"""
        ds = {w.get("date_added") for w in self.words.values() if w.get("date_added")}
        return sorted(ds, reverse=True)

    # ---------- 状态操作 ----------
    def clear_today(self):
        """清空今日单词：把所有 active 置 False（保留在单词本中）。返回被清空的数量。"""
        n = 0
        for w in self.words.values():
            if w.get("active"):
                w["active"] = False
                n += 1
        if n:
            self.save()
        return n

    def set_active(self, word, active=True):
        w = self.get(word)
        if w:
            w["active"] = active
            self.save()
            return True
        return False

    def activate_many(self, words, active=True):
        changed = False
        for word in words:
            w = self.get(word)
            if w and w.get("active") != active:
                w["active"] = active
                changed = True
        if changed:
            self.save()

    def record_review(self, word, correct):
        """记录一次复习结果。"""
        w = self.get(word)
        if not w:
            return
        w["review_count"] = w.get("review_count", 0) + 1
        if correct:
            w["correct_count"] = w.get("correct_count", 0) + 1
        w["last_review"] = datetime.now().isoformat(timespec="seconds")
        # 记录每日复习统计（用于折线图）
        today = date.today().isoformat()
        stats = self._data.setdefault("stats", {})
        day = stats.setdefault(today, {"reviewed": 0, "correct": 0})
        day["reviewed"] = day.get("reviewed", 0) + 1
        if correct:
            day["correct"] = day.get("correct", 0) + 1
        self.save()

    # ---------- 学习统计 ----------
    def added_by_day(self):
        """{日期: 当天新增单词数}，由各单词的 date_added 汇总。"""
        c = Counter(w.get("date_added") for w in self.words.values() if w.get("date_added"))
        return dict(c)

    def _stat(self, d):
        return self._data.get("stats", {}).get(d, {})

    def daily_series(self, days=14):
        """最近 days 天的 [(date, 新增, 复习次数, 答对次数), ...]（含今天）。"""
        added = self.added_by_day()
        today = date.today()
        out = []
        for i in range(days - 1, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            s = self._stat(d)
            out.append((d, added.get(d, 0), s.get("reviewed", 0), s.get("correct", 0)))
        return out

    def streak(self):
        """连续打卡天数（今天暂未学习不算断，从昨天往前数）。"""
        added = self.added_by_day()

        def active(d):
            return added.get(d, 0) > 0 or self._stat(d).get("reviewed", 0) > 0

        today = date.today()
        d = today
        if not active(d.isoformat()):
            d = today - timedelta(days=1)
        n = 0
        while active(d.isoformat()):
            n += 1
            d -= timedelta(days=1)
        return n

    def totals(self):
        """累计复习次数与答对次数（跨所有单词）。"""
        reviewed = sum(w.get("review_count", 0) for w in self.words.values())
        correct = sum(w.get("correct_count", 0) for w in self.words.values())
        return reviewed, correct

    def today_counts(self):
        """今日 (新增单词数, 复习次数)。"""
        d = date.today().isoformat()
        return self.added_by_day().get(d, 0), self._stat(d).get("reviewed", 0)
