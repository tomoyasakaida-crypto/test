# -*- coding: utf-8 -*-
"""
officee(オフィシー) 大阪オフィス物件 週次スクレイパー

抽出条件:
  ① 入居可能日が現在より MOVEIN_MIN_MONTHS ヶ月以上あと
  ② 住所に「大阪市」
  ③ 面積が MIN_TSUBO 坪以上

使い方:
  python scraper.py               # 本番実行（取得→判定→Excel更新）
  python scraper.py --selftest    # ネット無しでロジック検証（モックデータ）
  python scraper.py --inspect URL # 1ページをレンダリングして HTML/画像を debug/ に保存
                                  #  → セレクタ確定に使う

注意: officee は Cloudflare 保護 + robots.txt で /search を禁止しています。
      本スクリプトは許可されている /area 一覧ページのみを、実ブラウザで
      低頻度（週1・待機あり）に取得します。利用規約はご確認のうえ自己責任で。
"""
import sys
import time
import random
import argparse
from datetime import date

import config as C
from parsing import (
    extract_tsubo, extract_rent, extract_address, extract_move_in_text,
    parse_move_in, judge,
)
import excel_store


# ── Playwright は実行時に import（selftest ではブラウザ不要）──
def _new_browser(pw):
    browser = pw.chromium.launch(headless=C.HEADLESS, args=["--no-sandbox"])
    ctx = browser.new_context(
        user_agent=C.USER_AGENT, locale="ja-JP",
        viewport={"width": 1440, "height": 960},
    )
    ctx.set_default_navigation_timeout(C.NAV_TIMEOUT_SEC * 1000)
    return browser, ctx


def _polite_sleep():
    time.sleep(random.uniform(C.REQUEST_MIN_DELAY_SEC, C.REQUEST_MAX_DELAY_SEC))


def _goto_pass_cloudflare(page, url):
    """ページを開き、Cloudflare の『Just a moment』を通過するまで待つ。"""
    page.goto(url, wait_until="domcontentloaded")
    deadline = time.time() + C.CLOUDFLARE_WAIT_SEC
    while time.time() < deadline:
        title = (page.title() or "")
        if "Just a moment" not in title and "Attention Required" not in title:
            break
        page.wait_for_timeout(2000)
    page.wait_for_timeout(1500)
    return page


def _cards_from_page(page):
    """
    ページから物件カードのテキストと詳細URLを取り出す。
    SELECTORS['card'] が指定されていればそれを使い、
    未指定なら詳細リンクを起点にカードらしいブロックを推定する。
    """
    sel = C.SELECTORS
    cards = []
    if sel.get("card"):
        loc = page.locator(sel["card"])
        n = loc.count()
        for i in range(n):
            el = loc.nth(i)
            text = el.inner_text()
            href = _first_detail_href(el, sel)
            cards.append((text, href))
        return cards

    # フォールバック: 詳細リンクの祖先ブロックをカードとみなす
    import re
    links = page.locator(f"a")
    seen = set()
    for i in range(links.count()):
        a = links.nth(i)
        href = a.get_attribute("href") or ""
        if not re.search(C.DETAIL_HREF_REGEX, href):
            continue
        # リンクを含むカード相当の親を辿る
        block = a.locator(
            "xpath=ancestor-or-self::*[self::li or self::article "
            "or contains(@class,'item') or contains(@class,'card') "
            "or contains(@class,'List')][1]"
        )
        try:
            text = block.first.inner_text()
        except Exception:
            text = a.inner_text()
        key = (text[:60], href)
        if key in seen:
            continue
        seen.add(key)
        cards.append((text, _abs(href)))
    return cards


def _first_detail_href(el, sel):
    import re
    links = el.locator(sel.get("detail_link") or "a")
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href") or ""
        if re.search(C.DETAIL_HREF_REGEX, href):
            return _abs(href)
    return ""


def _abs(href):
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return C.BASE + ("" if href.startswith("/") else "/") + href


def _parse_card(text, href):
    return {
        "name": _guess_name(text),
        "address": extract_address(text),
        "tsubo": extract_tsubo(text),
        "rent": extract_rent(text),
        "move_in_text": extract_move_in_text(text),
        "detail_url": href,
        "_raw": text,
    }


def _guess_name(text):
    for line in (text or "").splitlines():
        line = line.strip()
        if line and "坪" not in line and "円" not in line and "大阪" not in line:
            return line[:60]
    return ""


def _fetch_move_in_from_detail(page, url):
    """詳細ページの募集要項から入居可能日テキストを拾う。"""
    try:
        _goto_pass_cloudflare(page, url)
        full = page.locator("body").inner_text()
    except Exception:
        return ""
    mi = extract_move_in_text(full)
    if mi:
        return mi
    # ラベル行を総当り
    import re
    for label in C.MOVEIN_LABELS:
        m = re.search(label + r"[\s：:]*([^\n]{1,24})", full)
        if m:
            return m.group(1).strip()
    return ""


def _has_next_page(page):
    for text in ["次へ", "次のページ", "»", "next"]:
        loc = page.locator(f"a:has-text('{text}')")
        if loc.count() > 0:
            return True
    return False


# ── 本番実行 ────────────────────────────────────────────────
def run():
    from playwright.sync_api import sync_playwright
    today = date.today()
    print(f"[officee] 実行日 {today}  条件: {C.MOVEIN_MIN_MONTHS}ヶ月以上先 / "
          f"{C.CITY_KEYWORD} / {C.MIN_TSUBO}坪以上")

    records = {}  # key -> rec（重複排除）
    with sync_playwright() as pw:
        browser, ctx = _new_browser(pw)
        page = ctx.new_page()
        for path in C.SIZE_RANGE_PATHS:
            for pnum in range(1, C.MAX_PAGES_PER_RANGE + 1):
                sep = "&" if "?" in path else "?"
                url = f"{C.BASE}{path}{sep}page={pnum}"
                print(f"  取得: {url}")
                try:
                    _goto_pass_cloudflare(page, url)
                except Exception as e:
                    print(f"    ! 取得失敗: {e}")
                    break
                cards = _cards_from_page(page)
                if not cards:
                    print("    （物件カードなし → このレンジ終了）")
                    break
                for text, href in cards:
                    rec = _parse_card(text, href)
                    key = excel_store.make_key(rec)
                    records.setdefault(key, rec)
                has_next = _has_next_page(page)
                _polite_sleep()
                if not has_next:
                    break

        # 入居日が未取得なら詳細ページで補完
        if C.FETCH_DETAIL_FOR_MOVEIN:
            for rec in records.values():
                if not rec.get("move_in_text") and rec.get("detail_url"):
                    rec["move_in_text"] = _fetch_move_in_from_detail(page, rec["detail_url"])
                    _polite_sleep()
        browser.close()

    matched, unknown = _classify(records.values(), today)
    counts = excel_store.update_workbook(C.OUTPUT_XLSX, matched, unknown, today)
    print(f"[officee] 完了: 合致 {len(matched)} 件 "
          f"(新規 {counts['new']} / 継続 {counts['kept']} / 掲載終了 {counts['gone']}) "
          f"、入居日不明 {len(unknown)} 件 → {C.OUTPUT_XLSX}")


def _classify(recs, today):
    matched, unknown = [], []
    for rec in recs:
        j = judge(rec, today, C.MOVEIN_MIN_MONTHS, C.CITY_KEYWORD, C.MIN_TSUBO)
        # 条件②③は満たすが入居日が不明なもの
        if j["cond2"] and j["cond3"] and j["cond1"] is None:
            if C.INCLUDE_UNKNOWN_MOVEIN:
                matched.append((rec, j))
            else:
                unknown.append((rec, j))
        elif j["pass_all"]:
            matched.append((rec, j))
    return matched, unknown


# ── inspect: セレクタ確定用の HTML/画像ダンプ ───────────────
def inspect(url):
    from playwright.sync_api import sync_playwright
    import os
    os.makedirs("debug", exist_ok=True)
    with sync_playwright() as pw:
        browser, ctx = _new_browser(pw)
        page = ctx.new_page()
        print(f"[inspect] {url} を取得中...")
        _goto_pass_cloudflare(page, url)
        title = page.title()
        html = page.content()
        with open("debug/page.html", "w", encoding="utf-8") as f:
            f.write(html)
        page.screenshot(path="debug/page.png", full_page=True)
        print(f"[inspect] title={title!r}")
        print(f"[inspect] HTML {len(html)} 文字 → debug/page.html")
        print("[inspect] スクショ → debug/page.png")
        if "Just a moment" in (title or ""):
            print("[inspect] ⚠ まだ Cloudflare チャレンジ中。HEADLESS=False や "
                  "CLOUDFLARE_WAIT_SEC を増やして再試行してください。")
        else:
            cards = _cards_from_page(page)
            print(f"[inspect] 推定カード数: {len(cards)}")
            for text, href in cards[:3]:
                print("  ── カード例 ──")
                print("  " + "\n  ".join(text.splitlines()[:6]))
                print("  detail:", href)
        browser.close()


# ── selftest: ネット無しでロジック検証 ─────────────────────
def selftest():
    from datetime import date
    today = date(2026, 7, 12)
    threshold = "2026-10-12"  # today + 3ヶ月

    mock = [
        # ① 3ヶ月以上先 / ② 大阪市 / ③ 30坪以上 → 合致
        {"name": "本町センタービル", "address": "大阪府大阪市中央区本町1-1-1",
         "tsubo": 42.5, "rent": "38万円", "move_in_text": "2026年11月1日",
         "detail_url": "https://officee.jp/detail/1001"},
        # 入居日が早すぎ → 除外
        {"name": "梅田早期ビル", "address": "大阪府大阪市北区梅田2-2",
         "tsubo": 55.0, "rent": "60万円", "move_in_text": "2026年8月1日",
         "detail_url": "https://officee.jp/detail/1002"},
        # 即入居 → 除外
        {"name": "難波即入居ビル", "address": "大阪府大阪市中央区難波3-3",
         "tsubo": 33.0, "rent": "30万円", "move_in_text": "即入居可",
         "detail_url": "https://officee.jp/detail/1003"},
        # 大阪市外（堺市）→ 除外
        {"name": "堺タワー", "address": "大阪府堺市堺区南瓦町4-4",
         "tsubo": 80.0, "rent": "50万円", "move_in_text": "2027年1月",
         "detail_url": "https://officee.jp/detail/1004"},
        # 30坪未満 → 除外
        {"name": "小規模ビル", "address": "大阪府大阪市西区9-9",
         "tsubo": 22.0, "rent": "18万円", "move_in_text": "2027年3月",
         "detail_url": "https://officee.jp/detail/1005"},
        # 条件②③OK・入居日不明 → 入居日不明シートへ
        {"name": "淀屋橋不明ビル", "address": "大阪府大阪市中央区淀屋橋5-5",
         "tsubo": 45.0, "rent": "40万円", "move_in_text": "応相談",
         "detail_url": "https://officee.jp/detail/1006"},
    ]

    print(f"[selftest] today={today}  threshold(3ヶ月先)={threshold}")
    ok = True
    expect_pass = {"本町センタービル"}
    expect_unknown = {"淀屋橋不明ビル"}

    matched, unknown = _classify(mock, today)
    got_pass = {r["name"] for r, _ in matched}
    got_unknown = {r["name"] for r, _ in unknown}

    print(f"  合致  期待={expect_pass} 実際={got_pass}")
    print(f"  不明  期待={expect_unknown} 実際={got_unknown}")
    if got_pass != expect_pass:
        ok = False; print("  ✗ 合致判定が不一致")
    if got_unknown != expect_unknown:
        ok = False; print("  ✗ 不明判定が不一致")

    # 個別パーサの確認
    checks = [
        ("2026年11月1日", "date", "2026-11-01"),
        ("2026年10月上旬", "date", "2026-10-05"),
        ("2026/12/1", "date", "2026-12-01"),
        ("即入居可", "immediate", "2026-07-12"),
        ("応相談", "unknown", ""),
    ]
    for text, ek, ed in checks:
        d, k = parse_move_in(text, today)
        ds = d.isoformat() if d else ""
        mark = "○" if (k == ek and ds == ed) else "✗"
        if mark == "✗":
            ok = False
        print(f"  {mark} parse('{text}') -> kind={k} date={ds} (期待 {ek}/{ed})")

    # 坪/賃料/住所抽出
    sample = "本町センタービル\n大阪府大阪市中央区本町1-1-1\n42.5坪 / 賃料 38万円 / 入居可能日 2026年11月1日"
    print(f"  坪={extract_tsubo(sample)} 賃料={extract_rent(sample)} 住所={extract_address(sample)}")
    assert extract_tsubo(sample) == 42.5
    assert "大阪市" in extract_address(sample)

    # Excel 出力を一時ファイルで検証（週次 upsert）
    import tempfile, os
    tmp = os.path.join(tempfile.mkdtemp(), "test.xlsx")
    c1 = excel_store.update_workbook(tmp, matched, unknown, today)
    print(f"  Excel 1回目: {c1}  -> {tmp}")
    # 2回目（同じデータ）: 継続になるはず
    from parsing import judge as _j
    c2 = excel_store.update_workbook(tmp, matched, unknown, date(2026, 7, 19))
    print(f"  Excel 2回目(1週間後・同一): {c2}")
    if not (c1["new"] == 1 and c2["kept"] == 1 and c2["new"] == 0):
        ok = False; print("  ✗ 週次 upsert（新規→継続）が想定外")

    print("[selftest] 結果:", "PASS ✅" if ok else "FAIL ❌")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="officee 大阪オフィス週次スクレイパー")
    ap.add_argument("--selftest", action="store_true", help="ネット無しでロジック検証")
    ap.add_argument("--inspect", metavar="URL", help="1ページをダンプしてセレクタ確認")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if args.inspect:
        inspect(args.inspect)
        return
    run()


if __name__ == "__main__":
    main()
