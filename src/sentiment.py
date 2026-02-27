import requests
from database import db

class SentimentAnalyzer:
    def __init__(self):
        self.api_url = "https://api.alternative.me/fng/?limit=1"

    def get_fear_and_greed_index(self) -> dict:
        """
        Consulta a API do Alternative.me para obter o índice de Fear & Greed.
        0-24 = Medo Extremo (Extreme Fear)
        25-46 = Medo (Fear)
        47-54 = Neutro (Neutral)
        55-74 = Ganância (Greed)
        75-100 = Ganância Extrema (Extreme Greed)
        """
        try:
            response = requests.get(self.api_url, timeout=5)
            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                current = data["data"][0]
                value = int(current["value"])
                classification = current["value_classification"]
                
                # Registra no BD SQLite
                db.log_sentiment(value, classification)
                
                return {"value": value, "classification": classification, "status": "success"}
        except Exception as e:
            print(f"[Sentiment] Erro ao buscar Fear & Greed: {e}")
            
        return {"value": 50, "classification": "Neutral", "status": "error"} # Default fallback

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print(analyzer.get_fear_and_greed_index())
