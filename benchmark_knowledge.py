"""知识点归纳基准测试"""
import urllib.request, json, sys, io, time
from difflib import get_close_matches
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

KEY = "sk-Sav7yLJqAZ6FxCiXy2kCOOSelXOiDceY1YzhtCNsJArcu1dx"
BASE = "https://aiberm.com/v1"
CORPUS_DIR = Path("data/corpus")

def load_corpus_ids():
    ids = []
    for f in sorted(CORPUS_DIR.iterdir()):
        if f.suffix == ".md":
            ids.append(f.name)
    return ids

def call_llm(query):
    data = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "输出问题涉及的知识点文档名。如: 004-导数的定义与几何意义.md, 012-定积分的定义与性质.md"},
            {"role": "user", "content": query}
        ],
        "max_tokens": 100, "temperature": 0
    }).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=data,
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + KEY}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = json.loads(r.read())['choices'][0]['message']['content'].strip()
            return [k.strip() for k in raw.split(",") if k.strip()]
    except:
        return [""]

tests = [
    ("什么是导数", ["004-导数的定义与几何意义.md"]),
    ("求极限lim(x->0)sinx/x", ["001-数列极限的定义与性质.md", "002-函数极限的概念与计算.md"]),
    ("矩阵的特征值和特征向量怎么求", ["031-特征值与特征向量.md"]),
    ("什么叫定积分", ["012-定积分的定义与性质.md"]),
    ("级数什么情况下收敛", ["086-常数项级数审敛.md", "067-无穷级数.md"]),
    ("二维随机变量的分布怎么算", ["049-二维随机变量.md"]),
    ("二次型怎么化成标准形", ["098-二次型标准化.md", "036-二次型及其标准形.md"]),
    ("格林公式和高斯公式区别", ["106-格林高斯斯托克斯公式.md"]),
    ("什么是泰勒展开", ["013-泰勒公式.md"]),
    ("怎么判断线性方程组有解", ["030-线性方程组.md"]),
]

corpus_ids = load_corpus_ids()
results = []
print(f"{'ID':<5} {'问题':<30} {'LLM输出':<40} {'归一化后':<40} {'通过':>4}")
print("-" * 130)

for i, (query, expected) in enumerate(tests, 1):
    raw = call_llm(query)
    validated = []
    for kid in raw:
        match = get_close_matches(kid.strip(), corpus_ids, n=1, cutoff=0.1)
        validated.append(match[0] if match else kid.strip())
    
    passed = any(e in " ".join(validated) for e in expected)
    results.append({"id": i, "query": query, "raw": raw, "validated": validated, "expected": expected, "passed": passed})
    
    raw_s = ",".join(raw)[:38]
    val_s = ",".join([v[:22] for v in validated])[:38]
    print(f"T{i:<4} {query[:28]:<30} {raw_s:<40} {val_s:<40} {'PASS' if passed else 'FAIL':>4}")
    time.sleep(0.2)

passed = sum(1 for r in results if r["passed"])
print(f"\n准确率: {passed}/{len(tests)} ({passed/len(tests)*100:.0f}%)")

# 保存JSON报告
report = {"tests": results, "accuracy": f"{passed}/{len(tests)}"}
Path("benchmarks/benchmark_knowledge_norm.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("报告: benchmarks/benchmark_knowledge_norm.json")
