from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline


DEFAULT_EMOTION_MODEL = "j-hartmann/emotion-english-distilroberta-base"



class EmotionAnalyzer:
    def __init__(self, model_name: str = DEFAULT_EMOTION_MODEL):
        # Hugging Face 모델 로딩 (한 번만)
        
        try:
            print("loading emotion model locally")
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                local_files_only=True 
            )
        except OSError:
            print("no emotion model found locally. download is needed.")
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name, 
                local_files_only=False
            )
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                local_files_only=True
            )
        except OSError:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, 
                local_files_only=False
            )
        
        self.pipe = pipeline(
            task="text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            top_k=None,  # 전체 감정 점수 보고 싶으면 None
        )

    def analyze(self, text: str):
        """
        text 하나 넣으면 감정 결과 리스트를 리턴.
        예: [{"label": "joy", "score": 0.82}, ...]
        """
        text = text.strip()
        if not text:
            return []

        result = self.pipe(text, truncation=True, max_length=512)

        # pipeline 출력 형태가 [ [ {...}, {...} ] ] 일 수도 있어서 한 번 풀어줌
        if isinstance(result, list) and len(result) == 1 and isinstance(result[0], list):
            return result[0]
        return result
