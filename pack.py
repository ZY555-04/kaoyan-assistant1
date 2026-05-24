"""自动打包脚本 - 生成部署用 ZIP"""
import zipfile, os, shutil
from pathlib import Path

ROOT = Path(__file__).parent
PACK_DIR = ROOT / "KaoyanRAG-v4.0"
ZIP_FILE = ROOT / "KaoyanRAG-v4.1.zip"

# 清理（如果文件被占用则跳过）
try:
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
except:
    pass
try:
    if ZIP_FILE.exists():
        ZIP_FILE.unlink()
except:
    pass

# 创建目录
for d in ["data/corpus", "data/corpus_demo", "skills", "templates", "test_data"]:
    (PACK_DIR / d).mkdir(parents=True, exist_ok=True)

print("[1/4] Copying core files...")
core_files = ["app.py", "admin.py", "requirements.txt", "SETUP.md", "DEPLOY.md"]
bat_files = ["启动.bat", "启动考研RAG_Streamlit.bat"]
for f in core_files + bat_files:
    src = ROOT / f
    if src.exists():
        shutil.copy2(src, PACK_DIR / f)

print("[2/4] Copying knowledge base...")
corpus = ROOT / "data" / "corpus"
count = 0
for f in sorted(corpus.iterdir()):
    if f.suffix.lower() == ".md":
        shutil.copy2(f, PACK_DIR / "data" / "corpus" / f.name)
        count += 1

# 拷贝 demo corpus
demo_corpus = ROOT / "data" / "corpus_demo"
for f in sorted(demo_corpus.iterdir()):
    if f.is_file():
        shutil.copy2(f, PACK_DIR / "data" / "corpus_demo" / f.name)
print(f"    {count} docs + {len(list(demo_corpus.iterdir()))} demo docs copied")

print("[3/4] Copying Skills...")
skills_dir = ROOT / "skills"
for skill in skills_dir.iterdir():
    if skill.is_dir() and not skill.name.startswith("_"):
        dest = PACK_DIR / "skills" / skill.name
        shutil.copytree(skill, dest, dirs_exist_ok=True)
        print(f"    {skill.name}")

print("[4/4] Copying templates...")
templates = ROOT / "templates"
for f in templates.iterdir():
    if f.is_file():
        shutil.copy2(f, PACK_DIR / f.name)

# 拷贝演示测试数据
test_data = ROOT / "test_data"
for f in test_data.iterdir():
    if f.name.startswith("hallucination_tests_demo"):
        shutil.copy2(f, PACK_DIR / "test_data" / f.name)

# 打 ZIP
print(f"\nCreating {ZIP_FILE.name}...")
with zipfile.ZipFile(ZIP_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in PACK_DIR.rglob("*"):
        if f.is_file():
            arcname = f.relative_to(ROOT)
            zf.write(f, arcname)

# 统计
total = sum(1 for _ in PACK_DIR.rglob("*") if _.is_file())
size = ZIP_FILE.stat().st_size

# 清理临时目录
shutil.rmtree(PACK_DIR)

print(f"\n{'='*50}")
print(f"Package ready: {ZIP_FILE.name}")
print(f"  Files: {total}")
print(f"  Size:  {size:,} bytes ({size/1024:.0f} KB)")
print(f"\nSend this file. Recipient unzips and reads SETUP.md")
