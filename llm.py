from __future__ import annotations

import os

from openai import OpenAI


def client() -> OpenAI:
    key = os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("请先设置环境变量 DEEPSEEK_API_KEY")
    return OpenAI(api_key=key, base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))


def rewrite_query(question: str) -> str:
    response = client().chat.completions.create(
        model=os.getenv("DEEPSEEK_REWRITE_MODEL", "deepseek-chat"),
        temperature=0,
        max_tokens=80,
        messages=[
            {"role": "system", "content": "把财报问题压缩成适合检索的关键词。保留公司、年份、指标、口径和同义词，只输出一行。"},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content.strip()


def answer(question: str, chunks: list[dict]) -> str:
    context = []
    for index, chunk in enumerate(chunks, 1):
        context.append(
            f'[{index}] {chunk["company"]}，2026年半年度报告，第{chunk["page"]}页，{chunk["section"]}\n{chunk["text"]}'
        )
    prompt = f"""问题：{question}

检索材料：
{chr(10).join(context)}

只依据材料回答。每个事实句末标注一个或多个出处编号，如[1]或[1][3]。
遇到母公司与合并口径、期间或单位不明确时必须说明，不得猜测。
材料不足时直接说明缺少什么，不要用常识补全。"""
    response = client().chat.completions.create(
        model=os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-chat"),
        temperature=0.1,
        max_tokens=900,
        messages=[
            {"role": "system", "content": "你是上市公司半年报问答助手，重视数字、单位、期间和合并口径。"},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()

