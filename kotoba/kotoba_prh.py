# -*- coding: utf-8 -*-
"""いくつもの言葉のパーツリストから prh の辞書を作る（かんばん20261017-0259）。

  python3 kotoba/kotoba_prh.py                    → kotoba/共通の言葉.md だけから作る
  python3 kotoba/kotoba_prh.py ファイル [ファイル…]  → 渡した .md を全部読んで作る

YAML を標準出力に、語の数を標準エラーに書く。
渡した .md の「## やめる言い方」の次の行を全部つなげ、「／」と「・」で分けて
1語ずつ prh のルール（expected と pattern）にする。同じ語が2つのファイルにあれば1つにする。
expected の決め方・pattern の絞り方（NARROW）・YAML の形は everyone-seed/EINOW の
scripts/kotoba_prh.py（main bba35dd）と同じ。違いは、読むファイルを引数で受けることだけ。
pattern は JavaScript（textlint）と Python（テスト）の両方で同じに読める正規表現にする。
後ろを見る形は長さが決まったものだけ使う。標準ライブラリだけで書く。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.join(HERE, "共通の言葉.md")

# パーツリストや APRAS の画面にある正式な言葉を止めないよう、この語だけ pattern を絞る。
NARROW = {
    # 「記録する・記録した」の形だけ（生育記録などの画面の名前は止めない）。
    "記録": "記録(?:する|した)",
    # 「カレンダーの札」は止めない。
    "①②などの札": "(?<!カレンダーの)札",
    # 窓口・入口・出口・人口・口座は止めない（入口は別の語として止める）。
    "口": "(?<![窓入出人])口(?!座)",
    # 漢字や「り」のあとに続く形（提出する・取り出す）は止めない。
    "出す": "(?<![一-鿿々り])出す",
    # 手段・階段・段落・値段などは止めない。
    "段1〜4": "(?<![手階値格普算別石])段(?![落階差取ボ])",
    # 北海道・道具・道路などは止めない（一本道は別の語として止める）。
    "道": "(?<![海本水鉄報歩坂国県軌柔剣茶書街])道(?![具路順府県理筋徳場])",
    # 育苗箱・g/箱（APRAS の画面の文字）は止めない。
    "箱": "(?<![苗/])箱",
}


def _section(text, heading, name):
    """「## 見出し」の次の、空でない最初の行。"""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == heading:
            for rest in lines[i + 1:]:
                if rest.strip():
                    return rest.strip()
    raise SystemExit(f"{name} に「{heading}」の行がありません。")


def _split(line):
    """「／」と「・」で分ける。（→…）の中の「・」では分けない。"""
    words, buf, depth = [], "", 0
    for ch in line:
        if ch == "（":
            depth += 1
        elif ch == "）":
            depth -= 1
        if depth == 0 and ch in "／・":
            words.append(buf.strip())
            buf = ""
        else:
            buf += ch
    words.append(buf.strip())
    return [w for w in words if w]


def _tables(text):
    """「使わない言い方」の列がある表の行を (言葉, [使わない言い方の語…]) で返す。"""
    rows, cols = [], None
    for line in text.splitlines():
        if not line.startswith("|"):
            cols = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cols is None:
            cols = cells
            continue
        if set("".join(cells)) <= set("-: ") or "使わない言い方" not in cols:
            continue
        word = cells[cols.index("言葉")]
        avoid = cells[cols.index("使わない言い方")]
        rows.append((word, [a.strip("（）") for a in re.split("[／・]", avoid)]))
    return rows


def read_files(paths=None):
    """[(ファイル名, 中身)…]。paths が無ければ kotoba/共通の言葉.md だけ。"""
    out = []
    for p in paths or [COMMON]:
        with open(p, encoding="utf-8") as f:
            out.append((p, f.read()))
    return out


def build_rules(texts=None):
    """[{"word", "expected", "pattern"}…] を、やめる言い方の行の順（ファイルの順）で返す。

    texts は [(ファイル名, 中身)…]。無ければ kotoba/共通の言葉.md だけを読む。
    """
    if texts is None:
        texts = read_files()
    rows, items = [], []
    for name, text in texts:
        rows += _tables(text)
        items += _split(_section(text, "## やめる言い方", name))
    rules, seen = [], set()
    for item in items:
        m = re.fullmatch(r"(.+?)（→(.+)）", item)
        word = m.group(1) if m else item
        if word in seen:
            continue
        seen.add(word)
        if m:
            expected = m.group(2)
        else:
            hits = [w for w, avoid in rows if word in avoid]
            expected = "／".join(hits) if hits else f"{word} は使わない（言葉のパーツリスト）"
        pattern = NARROW.get(word, re.escape(word))
        rules.append({"word": word, "expected": expected, "pattern": pattern})
    return rules


def _q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_yaml(rules):
    out = ["version: 1", "rules:"]
    for r in rules:
        out.append(f"  - expected: {_q(r['expected'])}")
        out.append(f"    pattern: {_q('/' + r['pattern'] + '/')}")
    return "\n".join(out) + "\n"


def main():
    rules = build_rules(read_files(sys.argv[1:]))
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdout.write(to_yaml(rules))
    sys.stderr.write(f"辞書の語の数：{len(rules)}\n")


if __name__ == "__main__":
    main()
