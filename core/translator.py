import time
from abc import ABC, abstractmethod
from queue import Queue, Empty
from PySide6.QtCore import QThread, Signal


# 1. 번역 엔진 전략 추상화 (Strategy Pattern)
class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, text: str) -> str:
        pass


class HuggingFaceTranslator(BaseTranslator):
    """오프라인 로컬 번역 (Helsinki-NLP/opus-mt-ko-en)"""
    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-ko-en"):
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # 웜업 (Cold Start 방지)
        dummy = self.tokenizer("웜업", return_tensors="pt")
        self.model.generate(**dummy)

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        inputs = self.tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
        outputs = self.model.generate(**inputs, max_new_tokens=512)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)


class GeminiTranslator(BaseTranslator):
    """클라우드 API 번역 (google-genai)"""
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        prompt = f"Translate the following Korean text to natural English for lecture translation:\n{text}"
        response = self.model.generate_content(prompt)
        return response.text.strip()


# 2. 비동기 번역 워커 스레드 (큐 감시 및 시그널 발행)
class TranslationEngine(QThread):
    translation_done = Signal(str, str, float)  # (원문, 번역문, 소요시간)
    error_occurred = Signal(str)

    def __init__(self, translator: BaseTranslator, request_queue: Queue):
        super().__init__()
        self.translator = translator
        self.request_queue = request_queue
        self.is_running = True

    def set_translator(self, translator: BaseTranslator):
        self.translator = translator

    def run(self):
        while self.is_running:
            try:
                text = self.request_queue.get(timeout=0.1)
                if text is None:
                    break

                start_time = time.perf_counter()
                translated_text = self.translator.translate(text)
                elapsed_time = time.perf_counter() - start_time

                self.translation_done.emit(text, translated_text, elapsed_time)
                self.request_queue.task_done()

            except Empty:
                continue
            except Exception as e:
                self.error_occurred.emit(f"번역 처리 오류: {str(e)}")

    def stop(self):
        self.is_running = False
        self.request_queue.put(None)
        self.wait()