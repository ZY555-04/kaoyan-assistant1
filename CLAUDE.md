# CLAUDE.md

## 项目概述

考研学习助手 — Streamlit 多用户 Web 应用。提供考研数学问答、英语专家、打卡督学、学习资料生成、费曼学习法、知识库等功能。API 使用小米 MiMo v2.5。

## 技术栈

- **Python** 3.13 (`C:\Users\H.D.B\AppData\Local\Python\bin\python.exe`)
- **框架**: Streamlit (无前后端分离，纯 `app.py`)
- **数据库**: SQLite `data/memory.db`（多用户隔离，`user_id` 区分）
- **API**: 小米 MiMo v2.5，endpoint `https://api.xiaomimimo.com/v1`，模型 `mimo-v2.5`
- **数学渲染**: KaTeX（本地 `file:///` 绝对路径，3 个文件在 `data/katex/`）
- **文档生成**: Pandoc（`python-docx` + `lxml`，模板 `data/reference/template.docx`）
- **部署**: 腾讯云 Ubuntu 服务器，`pack.py` 打包 ZIP

## 文件职责

| 文件 | 说明 |
|------|------|
| `app.py` | 主程序（~4700 行），包含全部页面、API 调用、CSS、数据库操作 |
| `knowledge_base.py` | 专业知识库模块（独立部署包，含 OCR、向量检索、出题） |
| `admin.py` | 管理员面板（用户管理、数据统计） |
| `recommend.py` | 同事 PR — 学习资料推荐模块 |
| `kaoyan_predict.py` | 高校热度预测引擎（Node.js 子进程） |
| `pack.py` | 打包脚本 → `KaoyanRAG-v4.2.zip`（含 corpus/skills/katex/predict） |
| `copy_to_git.py` | 从 dev 目录同步到 `C:\Users\H.D.B\Desktop\git\`，用于 GitHub 发布 |

## 关键架构

### 页面路由

通过 `st.session_state.page` 控制，各页面用 `if st.session_state.page == "xxx":` 守卫。

```
hub       → 备考看板（默认首页，快速入口卡片）
popularity→ 高校热度查询
english   → 考研英语专家（作文批改/长难句/翻译/单词）
checkin   → 打卡督学（打卡/日记/学习计划/番茄计时/学习画像）
material  → 学习资料（AI 生成习题册、DOCX 导出）
suggest   → 提建议
```

导航模式：Hub 页面的卡片按钮设置 `st.session_state.page` + `st.rerun()`。每页有「← 返回首页」按钮回到 hub。

### MiMo API 调用

- API Key 硬编码在 `app.py:38`
- 模型 `mimo-v2.5`（思维链模型，`content` 常为空，内容在 `reasoning_content` 字段）
- 统一使用 `_extract_content()` helper 读取回复（优先 `content`，空时 fallback `reasoning_content`）
- 流式调用：`stream=True`，yield `textContent`，打字效果每字 20-30ms
- `max_tokens` 默认 1500
- 所有 API 调用走 `call_llm_api(prompt, model="mimo-v2.5")` 或 `run_pipeline()` generator

### CSS 色系（当前橙色主题）

```css
主色: #D77757 (terra cotta orange) → #E8926A (渐变)
背景: #F8FAFC
卡片: #FFFFFF / #f8f9fa
学习卡片: #fff8f0 (学习中) / #f0faf4 (已掌握)
参考标签: #fef5f0, 文字 #8b5a3c
```

### 数据库

`data/memory.db` — SQLite，多用户隔离（所有查询带 `WHERE user_id=?`）。

主要表：`users`, `login_tokens`, `knowledge_mastery`, `qa_history`, `checkin_records`, `checkin_plans`, `checkin_diary`, `feynman_history` 等。

### KaTeX 渲染

- CDN fallback + 本地 `file:///` 绝对路径（3 文件：`katex.min.css`, `katex.min.js`, `auto-render.min.js`）
- `_fix_latex()` 预处理 LaTeX 字符串
- `_collapse_math()` 合并相邻 math 块
- `_escape_md()` 转义 Markdown 特殊字符
- `_katex_refresh()` 用 JavaScript 注入触发重新渲染

## API 配置

```python
API_KEY = "sk-c4f69ncnuomnc8pprclmhlasndea7tdjvxeo49jno3bzxpa6"
API_BASE = "https://api.xiaomimimo.com/v1"
MODEL = "mimo-v2.5"
MAX_TOKENS = 1500
```

## 登录系统

- Cookie 持久化（`extra-streamlit-components` CookieManager）
- `@st.cache_resource` + monkey-patch `check_cache_replay_rules` 避免 cookie 重复读写
- 登录/注册表单在文件开头，未登录时 `st.stop()`
- Token 有效期 30 天

## 部署

```bash
# 本地打包
python pack.py  # → KaoyanRAG-v4.2.zip (~200 文件, ~4MB)

# 服务器部署
scp KaoyanRAG-v4.2.zip ubuntu@111.229.102.178:/home/ubuntu/
ssh ubuntu@111.229.102.178
cd /home/ubuntu && python3 -c "import zipfile; zipfile.ZipFile('KaoyanRAG-v4.2.zip').extractall('kaoyan/')"
source /home/ubuntu/kaoyan/venv/bin/activate
pip install python-docx lxml -q
# 确保 Pandoc 已安装：apt install pandoc -y
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true > streamlit.log 2>&1 &
```

## 已知约束

- **页面标题保持「考研学习助手」不改**
- **不引入新的 pip 依赖**，保持最小依赖集
- MiMo 思维链模型：`content` 为空时用 `reasoning_content`，全局用 `_extract_content()` 处理
- `python-dotenv` 已移除，API Key 直接硬编码（避免服务器环境变量问题）
- 不 mock 纯函数模块，不引入 `as any` 到生产代码
- 打包时需确认 `data/katex/`、`data/reference/template.docx`、`templates/` 均被包含

## 最近改动

- 学习计划 prompt 去「老师」化：语气从亲切/有温度改为朴素/理性，禁用称呼（亲爱的同学/孩子/老师），格式从大段文字改为短段落+要点，字数 800→600
- Cookie 持久化登录、Pandoc DOCX 生成、知识库独立外包包
- 英语资料 7 分类、概念自测+解题评分、高校热度画像表单移至打卡督学
- MiMo API 全量切换（12 个 GLM 硬编码 → `mimo-v2.5`），`_extract_content()` 全局修复
