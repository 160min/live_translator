import sys
from pptx import Presentation

def parse_pptx_to_glossary(file_path):
    try:
        prs = Presentation(file_path)
        extracted_texts = []
        
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    # 텍스트 내 줄바꿈 및 다중 공백 제거
                    clean_text = " ".join(shape.text.split())
                    # 중복 제거
                    if clean_text not in extracted_texts:
                        extracted_texts.append(clean_text)
        
        # 콤마로 구분된 문자열 생성
        glossary = ", ".join(extracted_texts)
        print("--- Glossary 출력 ---")
        print(glossary)
        
    except Exception as e:
        print(f"PPTX 파싱 중 오류 발생: {e}")

if __name__ == "__main__":
    # 테스트용 PPTX 파일 경로를 지정하세요. (예: 'sample.pptx')
    sample_file = "sample.pptx"
    parse_pptx_to_glossary(sample_file)