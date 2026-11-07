
from dataclasses import dataclass, field
import time


@dataclass
class GlossaryHint:
    """
    PPT/PDF에서 추출한 강의 전공 키워드.
    STT와 번역 엔진 양쪽에서 공통으로 사용하는 문맥 데이터.
    """
    keywords: list[str]
    source_file: str
    extracted_at: float = field(default_factory=time.time)

    def to_prompt_string(self) -> str:
        """키워드를 AI 엔진에 전달할 문자열로 변환"""
        return ", ".join(self.keywords)


@dataclass
class TranscriptionResult:
    """STT 엔진의 음성 인식 결과"""
    chunk_id: int
    text: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class SubtitlePayload:
    """번역 엔진에서 GUI로 전달하는 최종 자막"""
    chunk_id: int
    original_text: str
    translated_text: str
    target_lang: str
    timestamp: float = field(default_factory=time.time)

    def to_display_text(self) -> str:
        return f"{self.original_text}\n{self.translated_text}"
