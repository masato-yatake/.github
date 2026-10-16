# -*- coding: utf-8 -*-
"""いくつもの言葉のパーツリストから prh の辞書を作る（かんばん20261017-0259）。

kotoba/kotoba_prh.py が作った辞書の pattern を Python の re で文に当てる。
文ごとの引っかかる数は、everyone-seed/EINOW の einow-demo/tests/test_seisan_kanban_20261016_1920.py の写し。

  python3 -m unittest kotoba/test_kotoba_prh.py
"""
import importlib.util
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "kotoba_prh", os.path.join(HERE, "kotoba_prh.py"))
kotoba_prh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kotoba_prh)

# 製品のリポジトリの言葉のパーツリストの代わり（EINOW だけにある「写し」「段1〜4」と、共通と重なる語）。
PRODUCT = ("製品の言葉.md", "## やめる言い方\n\n写し／押す・押せない／段1〜4／箱\n")

RULES_COMMON = kotoba_prh.build_rules()
RULES_BOTH = kotoba_prh.build_rules(kotoba_prh.read_files() + [PRODUCT])


def _hits(text, rules=RULES_BOTH):
    return sum(len(re.findall(r["pattern"], text)) for r in rules)


class TestHits(unittest.TestCase):
    CASES = [
        ("API の口を足す", 1),
        ("全体テストの結果を貼る", 0),
        ("カレンダーの札", 0),
        ("札を付ける", 1),
        ("生育記録を開く", 0),
        ("記録した", 1),
        ("履歴を提出する", 0),
        ("準備中ですを出す", 1),
        ("北海道", 0),
        ("道具", 0),
        ("手段", 0),
        ("育苗箱施用", 0),
        ("g/箱", 0),
        ("箱を足す", 1),
        ("部品の箱", 1),
    ]

    def test_hits(self):
        for text, n in self.CASES:
            with self.subTest(text=text):
                self.assertEqual(_hits(text), n)

    def test_goukakufuda_hits(self):
        self.assertGreaterEqual(_hits("合格札を貼る"), 1)


class TestWordCount(unittest.TestCase):
    def test_common_only(self):
        self.assertEqual(len(RULES_COMMON), 15)

    def test_with_product_dedup(self):
        # 写し・段1〜4 が加わり、押す・押せない・箱 は1つにまとまる。
        self.assertEqual(len(RULES_BOTH), 17)

    def test_yaml_has_every_rule(self):
        out = kotoba_prh.to_yaml(RULES_BOTH)
        self.assertTrue(out.startswith("version: 1\nrules:\n"))
        self.assertEqual(out.count("  - expected: "), 17)
        self.assertEqual(out.count("    pattern: \"/"), 17)


if __name__ == "__main__":
    unittest.main()
