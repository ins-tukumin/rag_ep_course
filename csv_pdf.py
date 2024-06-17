import os
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# CSVファイルの読み込み
csv_file = 'csvs/test_csv.csv'
df = pd.read_csv(csv_file)

# タイムスタンプ列を無視する
df = df.drop(columns=['タイムスタンプ'])

# 出力フォルダーの作成
output_folder = 'pdfsvector'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# PDFを作成する関数
def create_pdf(student_id, diary_entries):
    pdf_file_name = os.path.join(output_folder, f"{student_id}.pdf")
    doc = SimpleDocTemplate(pdf_file_name, pagesize=A4)
    
    # フォントの登録
    pdfmetrics.registerFont(TTFont('IPAexGothic', 'fonts/ipaexg.ttf'))
    
    # スタイルの取得とフォントの設定
    styles = getSampleStyleSheet()
    #styleN = styles['Normal']
    styleN = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName='IPAexGothic',
        fontSize=16,  # フォントサイズを14に設定
        leading=20,  # 行間を設定
    )
    styleN.fontName = 'IPAexGothic'
    
    # PDF要素のリスト
    elements = []
    
    #elements.append(Paragraph(f"学籍番号：{student_id}", styleN))
    elements.append(Spacer(1, 12))
    
    # 各エントリの出力
    for date, entry in diary_entries.items():
        elements.append(Paragraph(f"{date}:{entry}", styleN))
        elements.append(Spacer(1, 12))
    
    # PDFの生成
    doc.build(elements)
    print(f"PDF saved as {pdf_file_name}")

# データの整形
grouped = df.groupby('No')

for student_id, group in grouped:
    diary_entries = {}
    for col in group.columns:
        if col != 'No':
            entries = group[col].dropna().tolist()
            if entries:
                diary_entries[col] = " ".join(entries)
    create_pdf(student_id, diary_entries)
