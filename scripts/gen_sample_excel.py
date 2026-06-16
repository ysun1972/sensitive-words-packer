"""
生成演示用 Excel 敏感词表
用法: python scripts/gen_sample_excel.py
输出: sample/config/words_demo.xlsx
"""
import sys
from pathlib import Path

# 让 scripts/ 脚本能 import src/
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import openpyxl
except ImportError:
    print("需要 openpyxl: pip install openpyxl", file=sys.stderr)
    sys.exit(1)


def main():
    out_dir = Path(__file__).parent.parent / "sample" / "config"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "words_demo.xlsx"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "敏感词"

    # 表头
    ws.append(["部门", "类型", "敏感词"])
    # 数据
    data = [
        ["市场部", "客户", "AcmeCorp"],
        ["市场部", "客户", "Globex"],
        ["财务部", "账号", "6225880137460000"],
        ["财务部", "邮箱", "cfo@company.com"],
        ["研发部", "代号", "ProjectPhoenix"],
        ["研发部", "代号", "蓝海计划"],
    ]
    for row in data:
        ws.append(row)

    wb.save(out_path)
    print(f"已生成 {out_path}（{len(data)} 行数据）")


if __name__ == "__main__":
    main()
