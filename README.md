# 2026 年半导体半年报知识库

本项目按 2026 年 6 月 30 日 A 股申万半导体总市值前 20 家企业构建。流程包括半年报下载、逐页文字与表格提取、带标签切块、Qwen3 1024 维向量索引、BM25、DeepSeek 问答和 10 题评测。

## 1 安装

建议使用 Python 3.11。PowerShell：

```powershell
cd "本项目目录"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

若安装 `faiss-cpu` 失败，可改用 Conda 环境。不要把 API Key 写入源码。

## 2 下载 20 份半年报

```powershell
python download_reports.py
```

脚本从巨潮资讯查询“2026 年半年度报告”，过滤摘要和提示性公告，保存为：

```text
data/公司名/2026_半年报.pdf
```

下载结果写入 `download_manifest.json`。如果接口限制访问，按清单到巨潮资讯手动下载，并保持上述文件名。

## 3 提取与切块

```powershell
python extract.py
python chunk.py
```

`chunks.jsonl` 每行一个块，核心字段为 `company`、`section`、`page`、`chunk_id`、`text`。表格按行转为“列名: 值”，因此可以被“直销”“营业收入”等词命中。

## 4 建索引

```powershell
$env:EMBEDDING_MODEL="Qwen/Qwen3-Embedding-0.6B"
python index.py
```

RTX 2050 4GB 可先直接运行。若 CUDA 显存不足：

```powershell
$env:FORCE_CPU="1"
python index.py
```

CPU 模式可能需要几十分钟，但按 20 份半年报规模通常无需租服务器。若实测预计超过 3 小时，再考虑按小时租用 8GB 以上显存的 GPU 服务器。

## 5 配置 DeepSeek 并启动页面

```powershell
$env:DEEPSEEK_API_KEY="你的密钥"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com"
$env:DEEPSEEK_CHAT_MODEL="deepseek-chat"
$env:DEEPSEEK_REWRITE_MODEL="deepseek-chat"
streamlit run app.py
```

页面参考所给 PPT：左侧显示召回原文，右侧输入问题并显示带编号答案。每个编号对应原始公司、页码和文本块。

## 6 跑 10 题评测

```powershell
python eval.py
```

结果保存在 `evaluation/eval_results.csv`。脚本记录问题、召回公司、top-k 块和生成答案；“答对”“错因”“人工备注”保留给人工核验。错因统一填：

- 口径错：母公司与合并口径混淆
- 版本错：年份或报告版本错误
- 换词错：同义表达未命中
- 跨公司漏召回：全景题覆盖公司不足

## 计算量和费用

DeepSeek 只用于问题改写、回答和评测，不参与 PDF 提取与索引。先完成本地索引，再运行页面和评测可以控制 API token。跨公司问题的上下文最多使用 6 块，完整行业结论建议单独提高召回数量后再运行。

