from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Create a new Document
doc = Document()

# Define Title
title = doc.add_heading('BakeMap: 데이터 기반 베이커리 창업 입지 분석 서비스', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

doc.add_paragraph('서비스 기획안 / 사업 제안서 (고도화 버전)').alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph('작성일: 2025년 3월').alignment = WD_ALIGN_PARAGRAPH.CENTER

# 1. 서비스 개요
doc.add_heading('1. 서비스 개요', level=1)
doc.add_paragraph(
    "BakeMap은 서울시 인허가 데이터와 카드 매출 빅데이터를 결합하여, 베이커리 창업 예정자에게 "
    "단순 위치 정보 이상의 '매출 구조'와 '타겟 고객 분석'을 제공하는 업종 특화 상권 분석 플랫폼입니다."
)

# 2. 추가 분석 항목: 지역별 매출 구조
doc.add_heading('2. 지역별 매출 구조 및 수익성 분석', level=1)
table = doc.add_table(rows=1, cols=3)
table.style = 'Table Grid'
hdr_cells = table.rows[0].cells
hdr_cells[0].text = '상권 유형'
hdr_cells[1].text = '평균 월 매출'
hdr_cells[2].text = '매출 특징'

row_cells = table.add_row().cells
row_cells[0].text = '오피스/고급 주거 (강남, 서초)'
row_cells[1].text = '4,500 ~ 5,500만 원'
row_cells[2].text = '선물용 세트, 홀케이크 비중 높음 (객단가 상)'

row_cells = table.add_row().cells
row_cells[0].text = 'MZ 핫플레이스 (성수, 연남)'
row_cells[1].text = '3,500 ~ 4,200만 원'
row_cells[2].text = '트렌드 단품 메뉴(소금빵 등) 집중 소비'

row_cells = table.add_row().cells
row_cells[0].text = '일반 주거 단지 (노원, 은평)'
row_cells[1].text = '2,200 ~ 2,800만 원'
row_cells[2].text = '식사 대용 빵(식빵 등) 회전율 중심'

# 3. 시간대별 인기 메뉴 및 매출액
doc.add_heading('3. 시간대별 인기 메뉴 및 매출 추이', level=1)
doc.add_paragraph("매장 운영 효율화를 위한 시간대별 데이터 분석 결과를 제공합니다.")
doc.add_paragraph("- 오전 (07:00 ~ 10:00): 매출 20% | 인기메뉴: 샌드위치, 모닝커피 세트")
doc.add_paragraph("- 오후 (13:00 ~ 16:00): 매출 45% | 인기메뉴: 디저트류(타르트, 구움과자), 음료")
doc.add_paragraph("- 저녁 (17:00 ~ 20:00): 매출 35% | 인기메뉴: 식빵류, 홀케이크(기념일/퇴근길)")

# 4. 지역별 방문 연령대 분석
doc.add_heading('4. 지역별 매장 방문 연령대 데이터', level=1)
doc.add_paragraph(
    "입지에 따라 주 방문 고객층이 다르므로, 이에 맞춘 메뉴 구성 전략을 제안합니다."
)
doc.add_paragraph("• 2030 상권 (홍대, 성수, 이태원): SNS 가시성이 높은 화려한 비주얼의 디저트 메뉴 선호.")
doc.add_paragraph("• 3040 상권 (판교, 잠실, 마포): 자녀 간식용 건강빵(천연발효종, 통밀) 및 프리미엄 식재료 선호.")
doc.add_paragraph("• 5060 상권 (종로, 서촌, 전통주거지): 단팥빵, 맘모스빵 등 익숙한 맛과 부드러운 식감의 메뉴 선호.")

# 5. 핵심 기능 확장
doc.add_heading('5. 고도화된 서비스 기능', level=1)
doc.add_paragraph("1) 매출 예측 시뮬레이션: 선택 지역 입점 시 예상 월 매출 및 객단가 추정")
doc.add_paragraph("2) 타겟 고객 매칭: 내 레시피와 가장 잘 맞는 연령대가 밀집된 지역 추천")
doc.add_paragraph("3) 인벤토리 가이드: 시간대별 매출 추이에 따른 빵 생산 스케줄 권장")

# Save the document
file_path = "/mnt/data/BakeMap_Enhanced_Business_Plan.docx"
doc.save(file_path)

file_path
