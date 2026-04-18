from transformers import pipeline

# Load model once
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model="cardiffnlp/twitter-roberta-base-sentiment",
    tokenizer="cardiffnlp/twitter-roberta-base-sentiment"
)

LABEL_MAP = {
    "LABEL_0": "NEGATIVE",
    "LABEL_1": "NEUTRAL",
    "LABEL_2": "POSITIVE"
}

def analyze_sentiment(text: str):
    result = sentiment_pipeline(text[:512], truncation=True)[0]

    return {
        "label": LABEL_MAP[result["label"]],
        "score": round(result["score"], 3)
    }
