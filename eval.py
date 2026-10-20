from __future__ import annotations

import csv
from pathlib import Path

from common import EVAL_DIR, ensure_dirs
from llm import answer, rewrite_query
from retrieval import hybrid_search

QUESTIONS = [
    "中芯国际2026年上半年营业收入是多少？请使用合并口径。",
    "寒武纪2026年上半年归属于上市公司股东的净利润是多少？",
    "海光信息2026年上半年经营活动产生的现金流量净额是多少？",
    "北方华创2026年上半年研发费用是多少，占营业收入比例如何？",
    "兆易创新2026年上半年存储芯片业务收入是多少？",
    "中微公司2026年上半年合同负债期末余额是多少？",
    "澜起科技2026年上半年互连类芯片收入同比变化如何？",
    "长电科技2026年上半年境外收入是多少？不要误用母公司口径。",
    "2026年上半年这20家半导体公司普遍面临哪些经营问题？各公司如何应对？",
    "比较20家公司2026年上半年研发投入与经营现金流表现，哪些公司存在明显分化？",
]


def main() -> None:
    ensure_dirs()
    target = EVAL_DIR / "eval_results.csv"
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["题号", "问题", "检索词", "召回公司", "召回块", "答案", "答对", "错因", "人工备注"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for number, question in enumerate(QUESTIONS, 1):
            rewritten = rewrite_query(question)
            hits = hybrid_search(rewritten)
            generated = answer(question, hits)
            companies = list(dict.fromkeys(hit["company"] for hit in hits))
            refs = "; ".join(f'{h["company"]} p{h["page"]} {h["chunk_id"]}' for h in hits)
            writer.writerow({
                "题号": number, "问题": question, "检索词": rewritten,
                "召回公司": "、".join(companies), "召回块": refs, "答案": generated,
                "答对": "待人工判断", "错因": "", "人工备注": "",
            })
            print(f"完成 {number}/10：召回 {len(companies)} 家")
    print(target)


if __name__ == "__main__":
    main()

