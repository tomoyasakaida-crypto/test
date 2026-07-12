# -*- coding: utf-8 -*-
"""
officee スクレイパー設定ファイル。
ここだけ編集すれば抽出条件・出力先・取得ペースを調整できます。
CSS セレクタも下部でまとめて調整できます（初回のみ現地確認が必要）。
"""

# ── 抽出条件 ────────────────────────────────────────────────
# 条件① 入居可能日が「現在より何ヶ月以上あと」か
MOVEIN_MIN_MONTHS = 3

# 条件② 住所に含まれていれば残す文字列（大阪市のみ）
CITY_KEYWORD = "大阪市"

# 条件③ 面積（坪）の下限
MIN_TSUBO = 30.0

# ── 巡回対象 URL ────────────────────────────────────────────
# officee のエリア×坪数ページ。30坪以上を網羅するレンジ。
# 各レンジを ?page=1,2,3... とページングして巡回します。
BASE = "https://officee.jp"
SIZE_RANGE_PATHS = [
    "/area/p_osaka/30_50/",
    "/area/p_osaka/50_100/",
    "/area/p_osaka/100_200/",
    "/area/p_osaka/200_0/",   # 200坪以上（_0 = 上限開放）
]

# 1レンジあたり巡回する最大ページ数（保険。実際は「次ページ無し」で自動停止）
MAX_PAGES_PER_RANGE = 30

# ── 出力 ────────────────────────────────────────────────────
OUTPUT_XLSX = "output/officee_osaka_offices.xlsx"

# 入居可能日が判定できなかった物件の扱い
#   False … 一覧には載せず、別シート「入居日不明」に退避（推奨）
#   True  … 一覧にも載せる（条件①=△ として）
INCLUDE_UNKNOWN_MOVEIN = False

# ── 取得ペース（サイトに優しく）────────────────────────────
HEADLESS = True            # 画面を出したいときは False（Cloudflare 通過が安定する場合あり）
REQUEST_MIN_DELAY_SEC = 5  # ページ遷移ごとの待機（下限）
REQUEST_MAX_DELAY_SEC = 11 # ページ遷移ごとの待機（上限）
NAV_TIMEOUT_SEC = 60
CLOUDFLARE_WAIT_SEC = 25   # 「Just a moment」通過を待つ最大秒数
FETCH_DETAIL_FOR_MOVEIN = True  # 一覧に入居日が無い場合、詳細ページを開いて取得する

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# ── CSS セレクタ（★初回のみ現地確認して調整）────────────────
# `python scraper.py --inspect "<URL>"` を一度実行すると、
# レンダリング後の HTML とスクリーンショットを debug/ に保存します。
# それを見て以下を実サイトに合わせて確定してください。
# 空("")のままでも、カード内テキストへの正規表現フォールバックで
# 坪数・賃料・住所・入居日は拾えるように作ってあります。
SELECTORS = {
    # 1物件カードの繰り返し要素（最重要）
    "card": "",              # 例: "li.p-searchList__item" など
    # カード内の各項目（空なら card テキストから正規表現で抽出）
    "name": "",              # 建物名
    "address": "",           # 住所
    "detail_link": "a",      # 詳細ページへのリンク（href を使う）
    # 詳細ページの募集要項テーブル（入居可能日を拾う）
    "detail_spec_row": "tr", # 行要素
    "detail_spec_label": "th",
    "detail_spec_value": "td",
}

# 詳細ページ URL と判定するための href 正規表現（相対/絶対どちらも可）
DETAIL_HREF_REGEX = r"(/detail/|/building/|/bukken|/b_|/locations/|/estate/)"

# 募集要項で「入居可能日」を表すラベル候補
MOVEIN_LABELS = ["入居可能日", "入居時期", "入居予定", "入居可能時期", "空き予定", "入居", "現況"]
