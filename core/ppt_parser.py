from pptx import Presentation
from typing import List

def extract_keywords(file_path: str) -> List[str]:
    """
    [PPT 첨부] 이벤트 시 1회 호출되는 파싱 함수.
    PPTX 파일의 텍스트 노드 및 표 셀을 순회하여 중복을 제거한 키워드 리스트를 반환합니다.
    """
    extracted_texts: List[str] = []
    seen_texts = set()

    try:
        prs = Presentation(file_path)
        
        for slide in prs.slides:
            for shape in slide.shapes:
                # 일반 텍스트 상자 파싱
                if hasattr(shape, "text") and shape.text.strip():
                    for line in shape.text.splitlines():
                        clean_text = " ".join(line.split())
                        if clean_text and clean_text not in seen_texts:
                            seen_texts.add(clean_text)
                            extracted_texts.append(clean_text)

                # 표(Table) 내부 텍스트 파싱
                if shape.has_table:
                    for row in shape.table.rows:
                        for cell in row.cells:
                            clean_text = " ".join(cell.text.split())
                            if clean_text and clean_text not in seen_texts:
                                seen_texts.add(clean_text)
                                extracted_texts.append(clean_text)

    except Exception as e:
        raise RuntimeError(f"PPTX 파싱 실패 ({file_path}): {e}")

    return extracted_texts
