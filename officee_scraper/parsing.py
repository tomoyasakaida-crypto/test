# -*- coding: utf-8 -*-
"""
純ロジック（ネットワーク非依存）:
 - 日本語の入居可能日パース
 - 坪数 / 賃料 / 住所 の抽出
 - 3条件の判定
ここは scraper 本体を動かさなくても selftest で検証できます。
"""
import re
from datetime import date

# ── 月の加算（dateutil 非依存）──────────────────────────────
def add_months(d: date, n: int) -> date:
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    # 月末クランプ（例: 1/31 + 1ヶ月 = 2/28）
    import calendar
    day = min(d.day, calendar.monthrange(y, m)[1])
    return date(y, m, day)


# ── 入居可能日パース ────────────────────────────────────────
_IMMEDIATE = ["即", "即時", "即入居", "すぐ", "現況空", "空室", "空きあり", "現空"]
_UNKNOWN = ["相談", "応相談", "問合", "問い合わせ", "確認", "未定", "-", "―", "ー"]
_JUN = {"上旬": 5, "中旬": 15, "下旬": 25}


def parse_move_in(text: str, today: date):
    """
    戻り値: (parsed_date or None, kind)
      kind: "date" | "immediate" | "unknown"
    """
    if not text:
        return None, "unknown"
    t = text.strip()

    # 即入居系
    for kw in _IMMEDIATE:
        if kw in t:
            return today, "immediate"

    # YYYY年M月D日
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", t)
    if m:
        return _safe_date(m.group(1), m.group(2), m.group(3)), "date"

    # YYYY年M月（+ 上旬/中旬/下旬）
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月(上旬|中旬|下旬)?", t)
    if m:
        day = _JUN.get(m.group(3) or "", 1)
        return _safe_date(m.group(1), m.group(2), day), "date"

    # YYYY/M/D または YYYY-M-D
    m = re.search(r"(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})", t)
    if m:
        return _safe_date(m.group(1), m.group(2), m.group(3)), "date"

    # YYYY/M または YYYY-M
    m = re.search(r"(\d{4})[/\-.](\d{1,2})(?![/\-.\d])", t)
    if m:
        return _safe_date(m.group(1), m.group(2), 1), "date"

    # M月D日（年なし → 直近の未来年を推定）
    m = re.search(r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日", t)
    if m:
        mm, dd = int(m.group(1)), int(m.group(2))
        cand = _safe_date(today.year, mm, dd)
        if cand and cand < today:
            cand = _safe_date(today.year + 1, mm, dd)
        return cand, "date"

    for kw in _UNKNOWN:
        if kw in t:
            return None, "unknown"

    return None, "unknown"


def _safe_date(y, mo, d):
    try:
        y, mo, d = int(y), int(mo), int(d)
        import calendar
        d = min(d, calendar.monthrange(y, mo)[1])
        return date(y, mo, d)
    except (ValueError, TypeError):
        return None


# ── 各項目の抽出（カードテキストからの正規表現フォールバック）──
def extract_tsubo(text: str):
    """最大の坪数を返す（『10.5坪』『35.20 坪』などに対応）。"""
    vals = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*坪", text or "")]
    return max(vals) if vals else None


def extract_rent(text: str):
    """賃料テキスト（例 '35万円' / '350,000円'）をそのまま返す。"""
    m = re.search(r"(?:賃料|月額)?\s*([\d,]+(?:\.\d+)?\s*万?円)", text or "")
    return m.group(1).replace(" ", "") if m else ""


def extract_address(text: str):
    """住所らしき部分（大阪…市/区…）を返す。"""
    m = re.search(r"(大阪府[^\s\n、,]{2,40}|大阪市[^\s\n、,]{0,40})", text or "")
    return m.group(1) if m else ""


def extract_move_in_text(text: str):
    """カード/詳細テキストから入居可能日の記述を切り出す。"""
    for label in ["入居可能日", "入居時期", "入居予定", "入居可能時期", "空き予定"]:
        m = re.search(label + r"[：:\s]*([0-9０-９]{1,4}[^\n、,／|]{0,20})", text or "")
        if m:
            return m.group(1).strip()
    return ""


# ── 3条件の判定 ─────────────────────────────────────────────
def judge(record: dict, today: date, min_months: int, city_kw: str, min_tsubo: float):
    """
    record に keys: address, tsubo, move_in_text
    戻り値: dict(cond1, cond2, cond3, move_in_date, move_in_kind, pass_all)
      cond1/2/3 は True/False/None(不明)
    """
    threshold = add_months(today, min_months)

    # 条件②：住所に大阪市
    cond2 = (city_kw in (record.get("address") or ""))

    # 条件③：坪数 >= 下限
    tsubo = record.get("tsubo")
    cond3 = (tsubo is not None and tsubo >= min_tsubo)

    # 条件①：入居可能日 >= 今日+min_months
    d, kind = parse_move_in(record.get("move_in_text", ""), today)
    if kind == "immediate":
        cond1 = False
    elif kind == "date" and d is not None:
        cond1 = (d >= threshold)
    else:
        cond1 = None  # 不明

    pass_all = bool(cond1) and cond2 and cond3
    return {
        "cond1": cond1, "cond2": cond2, "cond3": cond3,
        "move_in_date": d.isoformat() if d else "",
        "move_in_kind": kind,
        "pass_all": pass_all,
    }
