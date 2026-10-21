# -*- coding: utf-8 -*-
"""Vocabulary Killer —— 本地背单词软件（PySide6 图形界面）。

功能：
  1. 录入当天要记的单词，自动从离线词库 ECDICT 生成中文释义 + 音标；
  2. 单词本永久保留；“清空今日单词”只清空当前学习列表，不删除任何词；
  3. 复习模式：显示中文释义 + 等量下划线(=字母数)，键入正确英文即过关；
     作答后按【空格】或【回车】切换下一个。

运行： python app.py     （打包后双击 Vocabulary Killer.exe）
"""
import os
import sys

from PySide6.QtCore import Qt, QTimer, QEvent, QPointF
from PySide6.QtGui import QFont, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication, QAbstractItemView, QCheckBox, QComboBox, QFrame,
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from dictionary import Dictionary, format_phonetic
from wordbook import WordBook

APP_TITLE = "Vocabulary Killer"

# 兼容 PyInstaller 打包：冻结后用 exe 所在目录，否则用脚本目录
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ACCENT = "#3b5bdb"

STYLE = """
* { font-family: "Microsoft YaHei UI","Segoe UI","Microsoft YaHei",sans-serif; }
QMainWindow { background: #eef1f7; }
QWidget { color: #1f2430; font-size: 14px; }

QLabel#appTitle { font-size: 23px; font-weight: 700; color: #2b3a67; }
QLabel#appSub   { font-size: 12px; color: #828a9c; }
QLabel#section  { font-size: 13px; font-weight: 600; color: #7a8194; }

QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab {
    background: transparent; color: #6b7280; padding: 10px 28px; margin: 4px 4px 8px 0;
    border: none; border-radius: 10px; font-size: 15px; font-weight: 600;
}
QTabBar::tab:selected { background: #ffffff; color: %(accent)s; }
QTabBar::tab:hover:!selected { color: %(accent)s; background: #e6ebfb; }

QGroupBox {
    background: #ffffff; border: 1px solid #e6e8ef; border-radius: 14px;
    margin-top: 16px; padding: 18px 16px 16px 16px; font-weight: 700; color: #2b3a67;
}
QGroupBox::title { subcontrol-origin: margin; left: 16px; padding: 0 6px; }

QPushButton {
    background: #ffffff; border: 1px solid #d7dbe6; border-radius: 9px;
    padding: 8px 18px; font-weight: 600; color: #3a4152;
}
QPushButton:hover { border-color: #9db2f5; color: %(accent)s; background: #f5f8ff; }
QPushButton:pressed { background: #e8eeff; }
QPushButton:disabled { color: #b6bcc9; background: #f2f3f7; border-color: #e6e8ef; }
QPushButton[accent="true"] { background: %(accent)s; border: 1px solid %(accent)s; color: #ffffff; }
QPushButton[accent="true"]:hover { background: #2f4bc0; border-color: #2f4bc0; color:#fff; }
QPushButton[accent="true"]:pressed { background: #27409f; }
QPushButton[accent="true"]:disabled { background: #aab6e8; border-color: #aab6e8; color: #eef1f7; }
QPushButton[danger="true"]:hover { border-color: #f0a3a3; color: #dc2626; background: #fff5f5; }

QLineEdit, QPlainTextEdit, QComboBox {
    background: #ffffff; border: 1px solid #d7dbe6; border-radius: 9px; padding: 8px 10px;
    selection-background-color: %(accent)s; selection-color: #fff;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border-color: %(accent)s; }
QLineEdit:disabled { background:#f2f3f7; color:#8a90a0; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #fff; border: 1px solid #d7dbe6; outline: 0;
    selection-background-color: #eef2ff; selection-color: %(accent)s;
}

QTableWidget {
    background: #ffffff; border: 1px solid #e6e8ef; border-radius: 12px;
    gridline-color: #eef0f5; alternate-background-color: #fafbfe;
}
QTableWidget::item { padding: 7px; border: none; }
QTableWidget::item:selected { background: #e7ecfb; color: #1f2430; }
QHeaderView::section {
    background: #f7f8fc; color: #55607a; padding: 9px; border: none;
    border-bottom: 1px solid #e6e8ef; font-weight: 700;
}
QTableCornerButton::section { background: #f7f8fc; border: none; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #cdd3e0; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #b3bacb; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }

QLabel#quizChinese {
    font-size: 28px; font-weight: 700; color: #1f2430; background: #ffffff;
    border: 1px solid #e6e8ef; border-radius: 16px; padding: 28px;
}
QLabel#quizBlanks { color: %(accent)s; background: transparent; }
QLabel#quizProgress { font-size: 14px; font-weight: 700; color: #6b7280; }
QLabel#quizScore { font-size: 14px; font-weight: 700; color: #6b7280; }
QLabel#quizFeedback { font-size: 19px; font-weight: 700; }
QLineEdit#answerEdit { font-size: 17px; padding: 11px; }
QStatusBar { background: #e7eaf1; color: #7a8194; }
QCheckBox { spacing: 6px; }

QFrame#statCard { background: #ffffff; border: 1px solid #e6e8ef; border-radius: 14px; }
QLabel#cheer {
    font-size: 14px; font-weight: 600; color: #3a4152;
    background: #f3f6ff; border: 1px solid #e2e9ff; border-radius: 10px; padding: 11px 14px;
}
QPushButton:checked { background: %(accent)s; border-color: %(accent)s; color: #ffffff; }
QPushButton:checked:hover { background: #2f4bc0; color: #ffffff; }
""" % {"accent": ACCENT}


def normalize(s):
    """归一化用于比对答案：去首尾空白、转小写、压缩内部空格。"""
    return " ".join((s or "").strip().lower().split())


def make_blanks(word):
    """按字母数生成下划线提示；多词短语按单词分组。"""
    groups = []
    for part in (word or "").split():
        letters = [c for c in part if c.isalpha() or c.isdigit()]
        n = len(letters) if letters else len(part)
        groups.append(" ".join(["_"] * max(n, 1)))
    return "     ".join(groups) if groups else "_"


# =====================================================================
# 录入单词
# =====================================================================
class AddTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        tip = QLabel("每行输入一个英文单词（可一次粘贴多个），点“查询释义”自动生成中文和音标，确认后加入单词本。")
        tip.setObjectName("section")
        tip.setWordWrap(True)
        root.addWidget(tip)

        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("例如：\napple\nabandon\ngive up")
        self.input.setMaximumHeight(130)
        root.addWidget(self.input)

        btns = QHBoxLayout()
        self.lookup_btn = QPushButton("① 查询释义")
        self.lookup_btn.clicked.connect(self.on_lookup)
        self.add_btn = QPushButton("② 添加到单词本")
        self.add_btn.setProperty("accent", True)
        self.add_btn.clicked.connect(self.on_add)
        self.both_btn = QPushButton("查询并添加")
        self.both_btn.setProperty("accent", True)
        self.both_btn.clicked.connect(self.on_lookup_and_add)
        clear_btn = QPushButton("清空")
        clear_btn.setProperty("danger", True)
        clear_btn.clicked.connect(self.on_clear)
        btns.addWidget(self.lookup_btn)
        btns.addWidget(self.add_btn)
        btns.addWidget(self.both_btn)
        btns.addStretch()
        btns.addWidget(clear_btn)
        root.addLayout(btns)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["单词", "音标", "中文释义", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        root.addWidget(self.table, 1)

        self.status = QLabel("")
        self.status.setObjectName("section")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

    def _typed_words(self):
        text = self.input.toPlainText()
        seen, out = set(), []
        for line in text.replace("，", "\n").replace(",", "\n").splitlines():
            w = line.strip()
            if not w:
                continue
            key = w.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(w)
        return out

    def on_lookup(self):
        words = self._typed_words()
        if not words:
            self.status.setText("请先输入至少一个单词。")
            return
        d = self.app.dict
        self.table.setRowCount(0)
        found = miss = 0
        for w in words:
            info = d.lookup(w) if d.available else None
            if info:
                phonetic = format_phonetic(info["phonetic"])
                translation = info["translation"] or info["definition"]
                status = "✓ 已找到"
                found += 1
            else:
                phonetic, translation = "", ""
                status = "✗ 未找到（可手动填写释义）" if d.available else "⚠ 词库不可用"
                miss += 1
            self._add_row(w, phonetic, translation, status, ok=bool(info))
        msg = "查询完成：找到 %d 个" % found
        if miss:
            msg += "，未找到 %d 个（音标/释义可在表格中直接手动编辑）" % miss
        if not d.available:
            msg = "词库不可用：%s" % (d.error or "未知错误")
        self.status.setText(msg)

    def _add_row(self, word, phonetic, translation, status, ok=True):
        r = self.table.rowCount()
        self.table.insertRow(r)
        w_item = QTableWidgetItem(word)
        w_item.setFlags(w_item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, 0, w_item)
        self.table.setItem(r, 1, QTableWidgetItem(phonetic))
        self.table.setItem(r, 2, QTableWidgetItem(translation))
        s_item = QTableWidgetItem(status)
        s_item.setFlags(s_item.flags() & ~Qt.ItemIsEditable)
        s_item.setForeground(Qt.darkGreen if ok else Qt.red)
        self.table.setItem(r, 3, s_item)

    def on_add(self):
        if self.table.rowCount() == 0:
            self.status.setText("没有可添加的行，请先查询。")
            return
        added = 0
        for r in range(self.table.rowCount()):
            word = self.table.item(r, 0).text().strip()
            phonetic = (self.table.item(r, 1).text().strip() if self.table.item(r, 1) else "")
            translation = (self.table.item(r, 2).text().strip() if self.table.item(r, 2) else "")
            if not word:
                continue
            self.app.book.add(word, phonetic, translation)
            added += 1
        self.status.setText("已加入单词本：%d 个（词本共 %d 个，今日 %d 个）。"
                            % (added, self.app.book.count(), len(self.app.book.active_words())))
        self.input.clear()
        self.table.setRowCount(0)
        self.app.book_tab.refresh()
        self.app.review_tab.refresh_dates()
        self.app.update_badge()

    def on_lookup_and_add(self):
        self.on_lookup()
        if self.table.rowCount():
            self.on_add()

    def on_clear(self):
        self.input.clear()
        self.table.setRowCount(0)
        self.status.setText("")


# =====================================================================
# 单词本
# =====================================================================
class BookTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(12)

        bar = QHBoxLayout()
        lab = QLabel("显示")
        lab.setObjectName("section")
        bar.addWidget(lab)
        self.filter = QComboBox()
        self.filter.addItem("今日单词", "today")
        self.filter.addItem("全部单词", "all")
        self.filter.addItem("指定日期", "date")
        self.filter.setMinimumWidth(120)
        self.filter.currentIndexChanged.connect(self.refresh)
        bar.addWidget(self.filter)
        self.date_combo = QComboBox()
        self.date_combo.currentIndexChanged.connect(self.refresh)
        self.date_combo.hide()
        bar.addWidget(self.date_combo)
        bar.addStretch()

        self.act_btn = QPushButton("设为今日")
        self.act_btn.clicked.connect(lambda: self.on_set_active(True))
        self.deact_btn = QPushButton("移出今日")
        self.deact_btn.clicked.connect(lambda: self.on_set_active(False))
        self.today_btn = QPushButton("清空今日单词")
        self.today_btn.setToolTip("把当前学习列表清零，单词仍保留在单词本中")
        self.today_btn.setProperty("danger", True)
        self.today_btn.clicked.connect(self.on_clear_today)
        self.del_btn = QPushButton("删除选中")
        self.del_btn.setProperty("danger", True)
        self.del_btn.clicked.connect(self.on_delete)
        for b in (self.act_btn, self.deact_btn, self.today_btn, self.del_btn):
            bar.addWidget(b)
        root.addLayout(bar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["单词", "音标", "中文释义", "录入日期", "今日", "复习(对/次)"])
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        root.addWidget(self.table, 1)

        self.summary = QLabel("")
        self.summary.setObjectName("section")
        root.addWidget(self.summary)

    def refresh(self):
        mode = self.filter.currentData()
        self.date_combo.setVisible(mode == "date")
        if mode == "date":
            cur = self.date_combo.currentText()
            self.date_combo.blockSignals(True)
            self.date_combo.clear()
            for d in self.app.book.dates():
                self.date_combo.addItem(d)
            if cur:
                i = self.date_combo.findText(cur)
                if i >= 0:
                    self.date_combo.setCurrentIndex(i)
            self.date_combo.blockSignals(False)

        if mode == "today":
            words = self.app.book.active_words()
        elif mode == "date":
            words = self.app.book.words_by_date(self.date_combo.currentText())
        else:
            words = self.app.book.all_words()

        self.table.setRowCount(0)
        for w in words:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(w.get("word", "")))
            self.table.setItem(r, 1, QTableWidgetItem(format_phonetic(w.get("phonetic", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(w.get("translation", "")))
            self.table.setItem(r, 3, QTableWidgetItem(w.get("date_added", "")))
            mark = QTableWidgetItem("●" if w.get("active") else "")
            mark.setTextAlignment(Qt.AlignCenter)
            mark.setForeground(Qt.darkGreen)
            self.table.setItem(r, 4, mark)
            self.table.setItem(r, 5, QTableWidgetItem(
                "%d/%d" % (w.get("correct_count", 0), w.get("review_count", 0))))

        self.summary.setText("当前显示 %d 个　·　单词本总计 %d 个　·　今日 %d 个"
                             % (len(words), self.app.book.count(), len(self.app.book.active_words())))

    def _selected_words(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()})
        out = []
        for r in rows:
            it = self.table.item(r, 0)
            if it:
                out.append(it.text())
        return out

    def on_clear_today(self):
        n = len(self.app.book.active_words())
        if n == 0:
            QMessageBox.information(self, "清空今日单词", "今日单词已经是空的。")
            return
        ret = QMessageBox.question(
            self, "清空今日单词",
            "将清空今日 %d 个单词（它们仍保留在单词本中，可随时复习）。继续？" % n,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.app.book.clear_today()
            self.refresh()
            self.app.review_tab.refresh_dates()
            self.app.update_badge()

    def on_delete(self):
        words = self._selected_words()
        if not words:
            QMessageBox.information(self, "删除选中", "请先在表格中选择要删除的单词。")
            return
        ret = QMessageBox.question(
            self, "删除选中",
            "将从单词本中永久删除 %d 个单词，确定？" % len(words),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ret == QMessageBox.Yes:
            for w in words:
                self.app.book.delete(w)
            self.refresh()
            self.app.review_tab.refresh_dates()
            self.app.update_badge()

    def on_set_active(self, active):
        words = self._selected_words()
        if not words:
            QMessageBox.information(self, "操作", "请先在表格中选择单词。")
            return
        self.app.book.activate_many(words, active)
        self.refresh()
        self.app.review_tab.refresh_dates()
        self.app.update_badge()


# =====================================================================
# 复习模式
# =====================================================================
class ReviewTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.queue = []
        self.idx = 0
        self.correct = 0
        self.wrong = 0
        self.wrong_words = []
        self.current = None
        self.answered = False
        self._build()
        self.refresh_dates()
        # 空格=下一个：安装全局事件过滤器（仅在复习答题且已作答时生效）
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Space:
            if self.isVisible() and self.stack.currentIndex() == 1 and self.answered:
                self.on_next()
                return True
        return super().eventFilter(obj, event)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        self.stack = QStackedWidget()
        root.addWidget(self.stack)

        # --- 页 0：设置 ---
        setup = QWidget()
        sv = QVBoxLayout(setup)
        sv.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("复习设置")
        bv = QVBoxLayout(box)
        bv.setSpacing(14)
        row1 = QHBoxLayout()
        rlab = QLabel("范围")
        rlab.setObjectName("section")
        row1.addWidget(rlab)
        self.scope = QComboBox()
        self.scope.addItem("今日单词", "today")
        self.scope.addItem("全部单词", "all")
        self.scope.addItem("指定日期", "date")
        self.scope.setMinimumWidth(130)
        self.scope.currentIndexChanged.connect(self._scope_changed)
        row1.addWidget(self.scope)
        self.date_pick = QComboBox()
        self.date_pick.setMinimumWidth(130)
        self.date_pick.hide()
        row1.addWidget(self.date_pick)
        self.random_chk = QCheckBox("随机顺序")
        row1.addWidget(self.random_chk)
        row1.addStretch()
        bv.addLayout(row1)

        self.scope_info = QLabel("")
        self.scope_info.setObjectName("section")
        bv.addWidget(self.scope_info)

        hint = QLabel("答题：看中文 → 按下划线字母数键入英文 → 回车确认；作答后按【空格】或【回车】进入下一个。")
        hint.setObjectName("section")
        hint.setWordWrap(True)
        bv.addWidget(hint)

        self.start_btn = QPushButton("开始复习")
        self.start_btn.setProperty("accent", True)
        self.start_btn.setMinimumHeight(46)
        self.start_btn.clicked.connect(lambda: self.start())
        bv.addWidget(self.start_btn)
        sv.addWidget(box)
        sv.addStretch()
        self.stack.addWidget(setup)

        # --- 页 1：答题 ---
        quiz = QWidget()
        qv = QVBoxLayout(quiz)
        qv.setContentsMargins(0, 0, 0, 0)
        qv.setSpacing(12)

        top = QHBoxLayout()
        self.progress_lbl = QLabel("")
        self.progress_lbl.setObjectName("quizProgress")
        self.score_lbl = QLabel("")
        self.score_lbl.setObjectName("quizScore")
        top.addWidget(self.progress_lbl)
        top.addStretch()
        top.addWidget(self.score_lbl)
        qv.addLayout(top)

        qv.addWidget(QLabel("中文释义"))
        self.chinese_lbl = QLabel("")
        self.chinese_lbl.setObjectName("quizChinese")
        self.chinese_lbl.setWordWrap(True)
        self.chinese_lbl.setAlignment(Qt.AlignCenter)
        self.chinese_lbl.setMinimumHeight(120)
        qv.addWidget(self.chinese_lbl)

        self.blanks_lbl = QLabel("")
        self.blanks_lbl.setObjectName("quizBlanks")
        self.blanks_lbl.setAlignment(Qt.AlignCenter)
        mono = QFont("Consolas")
        mono.setPointSize(28)
        mono.setBold(True)
        self.blanks_lbl.setFont(mono)
        qv.addWidget(self.blanks_lbl)

        ans_row = QHBoxLayout()
        self.answer_edit = QLineEdit()
        self.answer_edit.setObjectName("answerEdit")
        self.answer_edit.setPlaceholderText("键入英文单词，回车确认…")
        self.answer_edit.returnPressed.connect(self.on_enter)
        ans_row.addWidget(self.answer_edit, 1)
        self.submit_btn = QPushButton("确认")
        self.submit_btn.setProperty("accent", True)
        self.submit_btn.setMinimumHeight(44)
        self.submit_btn.clicked.connect(self.on_submit)
        ans_row.addWidget(self.submit_btn)
        qv.addLayout(ans_row)

        self.feedback = QLabel("")
        self.feedback.setObjectName("quizFeedback")
        self.feedback.setAlignment(Qt.AlignCenter)
        self.feedback.setMinimumHeight(34)
        qv.addWidget(self.feedback)

        nav = QHBoxLayout()
        self.reveal_btn = QPushButton("看答案")
        self.reveal_btn.clicked.connect(self.on_reveal)
        self.skip_btn = QPushButton("跳过")
        self.skip_btn.clicked.connect(self.on_skip)
        self.next_btn = QPushButton("下一个 ▶（空格）")
        self.next_btn.setProperty("accent", True)
        self.next_btn.clicked.connect(self.on_next)
        self.quit_btn = QPushButton("结束复习")
        self.quit_btn.setProperty("danger", True)
        self.quit_btn.clicked.connect(self.finish)
        nav.addWidget(self.reveal_btn)
        nav.addWidget(self.skip_btn)
        nav.addStretch()
        nav.addWidget(self.next_btn)
        nav.addWidget(self.quit_btn)
        qv.addLayout(nav)
        qv.addStretch()

        self.stack.addWidget(quiz)

    def _scope_changed(self):
        is_date = self.scope.currentData() == "date"
        self.date_pick.setVisible(is_date)
        if is_date:
            self.refresh_dates()
        self._update_scope_info()

    def refresh_dates(self):
        cur = self.date_pick.currentText()
        self.date_pick.blockSignals(True)
        self.date_pick.clear()
        for d in self.app.book.dates():
            self.date_pick.addItem(d)
        if cur:
            i = self.date_pick.findText(cur)
            if i >= 0:
                self.date_pick.setCurrentIndex(i)
        self.date_pick.blockSignals(False)
        self._update_scope_info()

    def _build_queue(self):
        mode = self.scope.currentData()
        book = self.app.book
        if mode == "today":
            words = book.active_words()
        elif mode == "date":
            words = book.words_by_date(self.date_pick.currentText())
        else:
            words = book.all_words()
        return list(words)

    def _update_scope_info(self):
        self.scope_info.setText("当前范围共 %d 个单词待复习。" % len(self._build_queue()))

    def start(self, only_words=None):
        # 只接受列表；按钮 clicked 可能传入 checked(bool)，此处一律忽略并重建队列
        words = only_words if isinstance(only_words, list) else self._build_queue()
        if not words:
            QMessageBox.information(self, "复习模式", "该范围内没有单词，先去录入或换个范围。")
            return
        if self.random_chk.isChecked() and only_words is None:
            import random
            random.shuffle(words)
        self.queue = words
        self.idx = 0
        self.correct = 0
        self.wrong = 0
        self.wrong_words = []
        self.stack.setCurrentIndex(1)
        self.load_current()

    def load_current(self):
        if self.idx >= len(self.queue):
            self.finish()
            return
        self.current = self.queue[self.idx]
        self.answered = False
        word = self.current.get("word", "")
        self.progress_lbl.setText("第 %d / %d 个" % (self.idx + 1, len(self.queue)))
        self.score_lbl.setText("✓ %d　✗ %d" % (self.correct, self.wrong))
        self.chinese_lbl.setText(self.current.get("translation") or "（无中文释义）")
        self.blanks_lbl.setText(make_blanks(word))
        self.feedback.setText("")
        self.answer_edit.clear()
        self.answer_edit.setEnabled(True)
        self.answer_edit.setFocus()
        self.submit_btn.setEnabled(True)
        self.reveal_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.next_btn.setEnabled(False)

    def on_enter(self):
        if not self.answered:
            self.on_submit()
        else:
            self.on_next()

    def _lock(self):
        self.answered = True
        self.answer_edit.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.reveal_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.next_btn.setEnabled(True)
        self.next_btn.setFocus()
        self.score_lbl.setText("✓ %d　✗ %d" % (self.correct, self.wrong))

    def on_submit(self):
        if self.answered or self.current is None:
            return
        ans = self.answer_edit.text()
        target = self.current.get("word", "")
        if not ans.strip():
            self.feedback.setText("请先输入答案")
            self.feedback.setStyleSheet("color:#dc2626;")
            return
        ok = normalize(ans) == normalize(target)
        self.app.book.record_review(target, ok)
        if ok:
            self.correct += 1
            self.feedback.setText("✓ 正确！　%s　%s" % (target, format_phonetic(self.current.get("phonetic", ""))))
            self.feedback.setStyleSheet("color:#16a34a;")
        else:
            self.wrong += 1
            self.wrong_words.append(self.current)
            self.feedback.setText("✗ 你答“%s”，正确答案：%s" % (ans.strip(), target))
            self.feedback.setStyleSheet("color:#dc2626;")
        self._lock()

    def on_reveal(self):
        if self.answered or self.current is None:
            return
        target = self.current.get("word", "")
        self.wrong += 1
        self.wrong_words.append(self.current)
        self.app.book.record_review(target, False)
        self.feedback.setText("答案：%s　%s" % (target, format_phonetic(self.current.get("phonetic", ""))))
        self.feedback.setStyleSheet("color:#dc2626;")
        self._lock()

    def on_skip(self):
        if self.current is None:
            return
        if not self.answered:
            self.wrong += 1
            self.wrong_words.append(self.current)
            self.app.book.record_review(self.current.get("word", ""), False)
            self.feedback.setText("已跳过　答案：%s" % self.current.get("word", ""))
            self.feedback.setStyleSheet("color:#dc2626;")
            self._lock()
        self.on_next()

    def on_next(self):
        self.idx += 1
        self.load_current()

    def finish(self):
        total = self.correct + self.wrong
        self.stack.setCurrentIndex(0)
        self._update_scope_info()
        self.app.book_tab.refresh()
        if total == 0:
            return
        detail = "本轮复习完成！\n\n答对：%d　答错：%d　共：%d\n正确率：%d%%" % (
            self.correct, self.wrong, total, round(self.correct * 100.0 / total))
        if self.wrong_words:
            names = "、".join(w.get("word", "") for w in self.wrong_words[:20])
            if len(self.wrong_words) > 20:
                names += " …"
            detail += "\n\n错词：%s" % names
        box = QMessageBox(self)
        box.setWindowTitle("复习结果")
        box.setText(detail)
        retry = None
        if self.wrong_words:
            retry = box.addButton("只练错词", QMessageBox.AcceptRole)
        box.addButton("关闭", QMessageBox.RejectRole)
        box.exec()
        if retry is not None and box.clickedButton() is retry:
            self.random_chk.setChecked(False)
            self.start(only_words=list(self.wrong_words))


# =====================================================================
# 学习统计：自绘折线图 + 概览卡片
# =====================================================================
class LineChart(QWidget):
    """自绘折线图（无第三方依赖，风格随主题）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        self.labels = []
        self.series = []  # [(名称, QColor, [数值])]

    def set_data(self, labels, series):
        self.labels = list(labels)
        self.series = series
        self.update()

    def _nice_max(self, maxv, steps=4):
        if maxv <= 0:
            return steps
        import math
        raw = maxv / steps
        base = 10 ** math.floor(math.log10(raw))
        step = 10 * base
        for m in (1, 2, 5, 10):
            if raw <= m * base:
                step = m * base
                break
        return int(step * steps)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 46, 18, 42, 36
        plot_w = max(w - ml - mr, 10)
        plot_h = max(h - mt - mb, 10)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawRoundedRect(0, 0, w, h, 14, 14)

        maxv = 0
        for _, _, vals in self.series:
            if vals:
                maxv = max(maxv, max(vals))
        ymax = self._nice_max(maxv)
        steps = 4
        p.setFont(QFont("Microsoft YaHei UI", 8))

        # 网格 + Y 轴刻度
        for i in range(steps + 1):
            val = ymax * i / steps
            y = mt + plot_h - plot_h * (i / steps)
            p.setPen(QPen(QColor("#eef0f5"), 1))
            p.drawLine(int(ml), int(y), int(ml + plot_w), int(y))
            p.setPen(QColor("#9aa0ae"))
            p.drawText(2, int(y) - 8, ml - 8, 16, Qt.AlignRight | Qt.AlignVCenter, str(int(val)))

        n = len(self.labels)

        def xpos(i):
            if n <= 1:
                return ml + plot_w / 2.0
            return ml + plot_w * i / (n - 1)

        # X 轴日期标签（自动抽稀）
        p.setPen(QColor("#9aa0ae"))
        lbl_step = (n + 6) // 7 if n else 1
        for i, lab in enumerate(self.labels):
            if i % lbl_step == 0 or i == n - 1:
                p.drawText(int(xpos(i)) - 32, int(mt + plot_h) + 8, 64, 18, Qt.AlignCenter, lab)

        # 折线 + 数据点
        for _name, color, vals in self.series:
            if not vals:
                continue
            pts = []
            for i in range(n):
                v = vals[i] if i < len(vals) else 0
                y = mt + plot_h - (plot_h * (v / ymax) if ymax > 0 else 0)
                pts.append((xpos(i), y))
            p.setPen(QPen(color, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for i in range(len(pts) - 1):
                p.drawLine(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1])
            p.setBrush(color)
            p.setPen(QPen(QColor("#ffffff"), 2))
            for (x, y) in pts:
                p.drawEllipse(QPointF(x, y), 4.0, 4.0)

        # 图例
        lx = ml
        p.setFont(QFont("Microsoft YaHei UI", 9))
        for name, color, _vals in self.series:
            p.setPen(Qt.NoPen)
            p.setBrush(color)
            p.drawRoundedRect(lx, 15, 12, 12, 3, 3)
            p.setPen(QColor("#4a5060"))
            p.drawText(lx + 18, 12, 140, 18, Qt.AlignLeft | Qt.AlignVCenter, name)
            lx += 18 + p.fontMetrics().horizontalAdvance(name) + 28
        p.end()


class StatCard(QFrame):
    """概览数字卡片。"""

    def __init__(self, caption, color="#3b5bdb", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(2)
        self.value = QLabel("0")
        self.value.setStyleSheet(
            "font-size:30px; font-weight:800; color:%s; background:transparent; border:none;" % color)
        self.cap = QLabel(caption)
        self.cap.setObjectName("section")
        lay.addWidget(self.value)
        lay.addWidget(self.cap)

    def set_value(self, v):
        self.value.setText(str(v))


class StatsTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.days = 14
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 18)
        root.setSpacing(14)

        cards = QHBoxLayout()
        cards.setSpacing(12)
        self.c_total = StatCard("单词本总数", "#2b3a67")
        self.c_today_add = StatCard("今日新增", "#3b5bdb")
        self.c_today_rev = StatCard("今日复习", "#16a34a")
        self.c_streak = StatCard("连续打卡(天)", "#f59e0b")
        self.c_acc = StatCard("复习正确率", "#7c3aed")
        for c in (self.c_total, self.c_today_add, self.c_today_rev, self.c_streak, self.c_acc):
            cards.addWidget(c)
        root.addLayout(cards)

        self.cheer = QLabel("")
        self.cheer.setObjectName("cheer")
        self.cheer.setWordWrap(True)
        root.addWidget(self.cheer)

        row = QHBoxLayout()
        title = QLabel("学习趋势")
        title.setStyleSheet("font-size:15px; font-weight:700; color:#2b3a67;")
        row.addWidget(title)
        row.addStretch()
        self.range_btns = {}
        for d in (7, 14, 30):
            b = QPushButton("近 %d 天" % d)
            b.setCheckable(True)
            b.setChecked(d == self.days)
            b.clicked.connect(lambda _=False, dd=d: self.set_days(dd))
            self.range_btns[d] = b
            row.addWidget(b)
        root.addLayout(row)

        self.chart = LineChart()
        root.addWidget(self.chart, 1)

    def set_days(self, d):
        self.days = d
        for k, b in self.range_btns.items():
            b.setChecked(k == d)
        self.refresh()

    def refresh(self):
        book = self.app.book
        total = book.count()
        ta, tr = book.today_counts()
        streak = book.streak()
        reviewed, correct = book.totals()
        self.c_total.set_value(total)
        self.c_today_add.set_value(ta)
        self.c_today_rev.set_value(tr)
        self.c_streak.set_value(streak)
        self.c_acc.set_value(("%d%%" % round(correct * 100.0 / reviewed)) if reviewed else "—")
        self.cheer.setText(self._cheer_text(streak, ta, tr, total, reviewed, correct))

        data = book.daily_series(self.days)
        labels = [row[0][5:] for row in data]  # MM-DD
        added = [row[1] for row in data]
        reviewed_d = [row[2] for row in data]
        self.chart.set_data(labels, [
            ("新增单词", QColor("#3b5bdb"), added),
            ("复习次数", QColor("#16a34a"), reviewed_d),
        ])

    def _cheer_text(self, streak, ta, tr, total, reviewed, correct):
        parts = []
        if streak >= 3:
            parts.append("🔥 连续打卡 %d 天，太强了，继续保持！" % streak)
        elif streak == 2:
            parts.append("🔥 已连续打卡 2 天，明天就是三连击！")
        elif streak == 1:
            parts.append("✅ 今天已打卡，坚持就是胜利！")
        else:
            parts.append("💪 今天还没开始，记几个单词打个卡吧！")
        if ta:
            parts.append("今日新增 %d 词" % ta)
        if tr:
            parts.append("复习 %d 次" % tr)
        if reviewed:
            parts.append("累计正确率 %d%%" % round(correct * 100.0 / reviewed))
        if total:
            parts.append("词本累计 %d 词" % total)
        return "　·　".join(parts)


# =====================================================================
# 主窗口
# =====================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(960, 680)
        self.setMinimumSize(760, 540)
        self.dict = Dictionary()
        self.book = WordBook()

        central = QWidget()
        cv = QVBoxLayout(central)
        cv.setContentsMargins(20, 16, 20, 10)
        cv.setSpacing(4)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        t = QLabel("📖  Vocabulary Killer")
        t.setObjectName("appTitle")
        s = QLabel("本地离线背单词 · 录入自动生成释义音标 · 看中文拼英文")
        s.setObjectName("appSub")
        title_box.addWidget(t)
        title_box.addWidget(s)
        header.addLayout(title_box)
        header.addStretch()
        self.count_badge = QLabel("")
        self.count_badge.setObjectName("appSub")
        header.addWidget(self.count_badge, 0, Qt.AlignBottom)
        cv.addLayout(header)

        tabs = QTabWidget()
        self.tabs = tabs
        self.add_tab = AddTab(self)
        self.book_tab = BookTab(self)
        self.review_tab = ReviewTab(self)
        self.stats_tab = StatsTab(self)
        tabs.addTab(self.add_tab, "　录入单词　")
        tabs.addTab(self.book_tab, "　单词本　")
        tabs.addTab(self.review_tab, "　复习模式　")
        tabs.addTab(self.stats_tab, "　学习统计　")
        tabs.currentChanged.connect(self._on_tab_changed)
        cv.addWidget(tabs, 1)
        self.setCentralWidget(central)

        self.update_badge()

        sb = self.statusBar()
        if self.dict.available:
            sb.showMessage("词库已就绪 · %s · 全程离线" % os.path.basename(self.dict.db_path or ""))
        else:
            sb.showMessage("⚠ %s" % (self.dict.error or "词库不可用"))
            QTimer.singleShot(300, self._warn_no_dict)

    def update_badge(self):
        self.count_badge.setText("单词本 %d 词　·　今日 %d 词"
                                 % (self.book.count(), len(self.book.active_words())))

    def _on_tab_changed(self, index):
        # 打开统计页时刷新数据（录入/复习后数字与折线图保持最新）
        if self.tabs.widget(index) is self.stats_tab:
            self.stats_tab.refresh()

    def _warn_no_dict(self):
        QMessageBox.warning(
            self, "词库未就绪",
            "未检测到 ECDICT 离线词库（stardict.db）。\n\n"
            "请把词库文件放到程序所在目录：\n%s\n\n"
            "在准备好词库之前，录入时无法自动生成中文释义和音标（可手动填写）。"
            % BASE_DIR)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setStyleSheet(STYLE)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
