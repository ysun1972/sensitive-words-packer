"""生成示例 PDF 文件（用于演示 PDF 脱敏）"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
out = Path(__file__).parent.parent / "sample" / "input" / "report.pdf"
out.parent.mkdir(parents=True, exist_ok=True)

doc = SimpleDocTemplate(str(out), pagesize=A4)
styles = getSampleStyleSheet()
body = ParagraphStyle("CN", parent=styles["BodyText"], fontName="STSong-Light", fontSize=10, leading=14)
content = [
    Paragraph("客户档案：李四", body),
    Paragraph("联系电话：18612345678", body),
    Paragraph("电子邮箱：admin@company.com", body),
    Paragraph("内部代号：蓝海计划 / ProjectPhoenix", body),
    Paragraph("银行卡号：6222021234567890123", body),
    Paragraph("身份证：440301199001011234", body),
    Paragraph("服务器 IP：192.168.1.100", body),
]
doc.build(content)
print(f"✓ 生成: {out}")
