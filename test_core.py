import sys
from queue import Queue
from core.ppt_parser import extract_keywords
from core.translator import HuggingFaceTranslator

def main():
    print("=== Core 모듈 기능 검증 시작 ===")
    
    # 1. PPT 파싱 모듈 검증
    ppt_path = "ppt/sample.pptx"
    print(f"\n1. [{ppt_path}] 키워드 추출 테스트...")
    try:
        keywords = extract_keywords(ppt_path)
        print(f"   ✅ 파싱 성공! 총 {len(keywords)}개 키워드 추출됨")
        print(f"   -> 추출 키워드 일부: {keywords[:3]}")
    except Exception as e:
        print(f"   ❌ 파싱 오류: {e}")

    # 2. 번역 엔진 모듈 검증
    print("\n2. 번역 엔진(HuggingFace) 로드 및 번역 테스트...")
    try:
        translator = HuggingFaceTranslator()
        test_text = "인공지능의 기본 개념과 수학적 도구를 학습합니다."
        translated = translator.translate(test_text)
        print("   ✅ 번역 성공!")
        print(f"   -> 원문: {test_text}")
        print(f"   -> 번역: {translated}")
    except Exception as e:
        print(f"   ❌ 번역 오류: {e}")

    print("\n=== 모든 모듈 검증 완수 완료 ===")

if __name__ == "__main__":
    main()