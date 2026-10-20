from __future__ import annotations

import html
import os

import streamlit as st

from llm import answer, rewrite_query
from retrieval import hybrid_search

st.set_page_config(page_title="2026 半年报 RAG", page_icon="报", layout="wide")
st.markdown("""
<style>
.stApp {background:#f4f7f6;color:#183238}.block-container{padding-top:1.8rem;max-width:1500px}
.hero{font-size:36px;font-weight:750;letter-spacing:-1px;margin:0}.sub{color:#6c7e80;margin:.4rem 0 1.4rem}
.metric{font-size:25px;font-weight:700}.muted{color:#75878a;font-size:13px}
.source{background:white;border:1px solid #dfe8e6;border-radius:12px;padding:14px;margin:10px 0}
.answer{background:#eff8f5;border-left:4px solid #008b72;padding:18px;border-radius:8px;font-size:17px;line-height:1.8}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero">看见一个答案的来处</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">2026 年半年报混合检索：问题改写、向量召回、BM25、出处核验</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.markdown('<div class="metric">20</div><div class="muted">家公司</div>', unsafe_allow_html=True)
c2.markdown('<div class="metric">1024</div><div class="muted">维向量</div>', unsafe_allow_html=True)
c3.markdown('<div class="metric">20 + 20</div><div class="muted">双路召回</div>', unsafe_allow_html=True)
c4.markdown('<div class="metric">6</div><div class="muted">块进入答案</div>', unsafe_allow_html=True)

st.divider()
left, right = st.columns([1.08, .92], gap="large")
with right:
    st.subheader("让问题走一遍 RAG")
    question = st.text_area("问题", placeholder="例如：兆易创新2026年上半年营业收入是多少？采用合并口径。", height=110)
    run = st.button("开始检索", type="primary", use_container_width=True)

if run and question.strip():
    if not os.getenv("DEEPSEEK_API_KEY"):
        st.error("尚未设置 DEEPSEEK_API_KEY。请在启动 Streamlit 的同一 PowerShell 窗口中设置。")
        st.stop()
    with st.spinner("正在改写问题并执行混合检索"):
        rewritten = rewrite_query(question.strip())
        hits = hybrid_search(rewritten)
        generated = answer(question.strip(), hits)
    with right:
        st.caption("检索表达式")
        st.code(rewritten, language=None)
        st.markdown("#### 回答")
        st.markdown(f'<div class="answer">{html.escape(generated).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
    with left:
        st.subheader("召回原文")
        for index, hit in enumerate(hits, 1):
            with st.expander(f'[{index}] {hit["company"]} · p{hit["page"]} · {hit["section"]} · {hit["score"]:.3f}', expanded=index <= 2):
                st.write(hit["text"])
                st.caption(hit["source_pdf"])
else:
    with left:
        st.subheader("召回原文")
        st.info("提交问题后，这里显示前 6 个原文块。")

