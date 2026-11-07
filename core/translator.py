import time
from pptx import Presentation
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

def main():
    # 1. PPT 파싱
    print("1. PPT 파싱 중...")
    prs = Presentation("sample.pptx")
    extracted_texts = []
    
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                clean_text = " ".join(shape.text.split())
                if clean_text not in extracted_texts:
                    extracted_texts.append(clean_text)
    
    print(f"추출 완료! 총 항목 수: {len(extracted_texts)}개\n")

    # 2. 번역 모델 로드
    print("2. 번역 모델 로드 중...")
    model_name = "Helsinki-NLP/opus-mt-ko-en"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # 웜업 (초기 연산 지연 방지)
    _ = model.generate(**tokenizer("웜업", return_tensors="pt"))

    # 3. 항목별 순차 번역 (상위 20개 테스트)
    # 292개 전체를 번역하시려면 아래 [:20] 문구를 제거하세요.
    target_list = extracted_texts[:20] 
    
    print(f"3. 상위 {len(target_list)}개 항목 번역 시작...\n")
    print("=" * 60)
    
    start_time = time.perf_counter()
    
    for i, text in enumerate(target_list, 1):
        inputs = tokenizer(text, return_tensors="pt", max_length=128, truncation=True)
        outputs = model.generate(**inputs)
        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"[{i:02d}] 원문: {text}")
        print(f"     번역: {translated}")
        print("-" * 60)
        
    end_time = time.perf_counter()
    
    total_time = end_time - start_time
    avg_time = total_time / len(target_list)
    
    print("\n--- 번역 성능 검증 결과 ---")
    print(f"번역한 항목 수: {len(target_list)}개")
    print(f"전체 소요 시간: {total_time:.4f}초")
    print(f"1개 문장당 평균 번역 속도: {avg_time:.4f}초")

if __name__ == "__main__":
    main()