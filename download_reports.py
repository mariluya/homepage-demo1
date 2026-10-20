from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from common import DATA_DIR, ROOT, ensure_dirs, load_companies

CNINFO_QUERY = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC = "https://static.cninfo.com.cn/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.cninfo.com.cn/",
}

def fetch_org_id(code: str) -> str:
    """用股票代码从巨潮 topSearch 接口反查 orgId"""
    url = "https://www.cninfo.com.cn/new/information/topSearch/query"
    payload = {"keyWord": code, "maxNum": 10}
    r = requests.post(url, data=payload, headers=HEADERS, timeout=15)
    for item in r.json():
        if item.get("code") == code:
            return item["orgId"]
    raise ValueError(f"未找到 {code} 的 orgId")

def market_for(code: str) -> str:
    return "sse" if code.startswith("6") else "szse"


def query_cninfo(company: dict) -> list[dict]:
    org_id = company.get("org_id") or fetch_org_id(company["code"])
    payload = {
        "pageNum": 1,
        "pageSize": 30,
        "column": market_for(company["code"]),
        "tabName": "fulltext",
        "plate": "",
        "stock": f'{company["code"]},{org_id}',
        "searchkey": "",  # 先清空 searchkey
        "category": "category_bndbg_szsh;",
        "trade": "",
        "seDate": "2026-06-01~2026-09-30",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    response = requests.post(CNINFO_QUERY, data=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json().get("announcements") or []


def choose_full_report(items: list[dict]) -> dict | None:
    candidates = []
    for item in items:
        title = BeautifulSoup(item.get("announcementTitle", ""), "html.parser").get_text()
        if "2026年半年度报告" not in title:
            continue
        if any(word in title for word in ("摘要", "提示性", "英文版")):
            continue
        candidates.append(item)
    return candidates[0] if candidates else None


def download_one(company: dict, overwrite: bool = False) -> dict:
    folder = DATA_DIR / company["name"]
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "2026_半年报.pdf"
    if target.exists() and target.stat().st_size > 100_000 and not overwrite:
        return {**company, "status": "exists", "path": str(target)}

    item = choose_full_report(query_cninfo(company))
    if not item:
        return {**company, "status": "not_found"}
    adjunct = item["adjunctUrl"].lstrip("/")
    url = CNINFO_STATIC + adjunct
    with requests.get(url, headers=HEADERS, timeout=90, stream=True) as response:
        response.raise_for_status()
        with target.open("wb") as handle:
            for block in response.iter_content(1024 * 1024):
                if block:
                    handle.write(block)
    return {
        **company,
        "status": "downloaded",
        "path": str(target),
        "url": url,
        "title": re.sub("<.*?>", "", item.get("announcementTitle", "")),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    results = []
    for company in load_companies():
        print(f'[{company["rank"]:02d}/20] {company["name"]}')
        try:
            result = download_one(company, overwrite=args.overwrite)
        except Exception as exc:
            result = {**company, "status": "error", "error": str(exc)}
        results.append(result)
        print(" ", result["status"])
        time.sleep(0.8)
    (ROOT / "download_manifest.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    missing = [r["name"] for r in results if r["status"] not in {"exists", "downloaded"}]
    print(f"完成：{len(results) - len(missing)}/20")
    if missing:
        print("需手动补充：" + "、".join(missing))


if __name__ == "__main__":
    main()

