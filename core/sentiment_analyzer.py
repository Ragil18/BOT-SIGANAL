import os
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# Optional: Use VADER sentiment analyzer from NLTK
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    _vader = SentimentIntensityAnalyzer()
except Exception:
    _vader = None

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def score_text(text: str) -> float:
    """Score a single string between -1.0 and 1.0 using VADER or keyword heuristics."""
    if not text:
        return 0.0
    if _vader:
        return float(_vader.polarity_scores(text)['compound'])
    
    pos_words = {"gain", "up", "rise", "bull", "bullish", "surge", "profit", "positive", "high", "rally", "record", "jump", "boom", "soar"}
    neg_words = {"lose", "loss", "down", "fall", "bear", "bearish", "drop", "negative", "low", "crash", "dump", "plunge", "slump", "fear", "crisis", "tensions"}
    
    low = text.lower()
    score = 0.0
    for w in pos_words:
        if w in low:
            score += 0.3
    for w in neg_words:
        if w in low:
            score -= 0.3
    return max(min(score, 1.0), -1.0)


def fetch_news_headlines(symbol: str, limit: int = 10) -> List[str]:
    """Fetch recent news headlines as a list of strings."""
    articles = fetch_structured_news(symbol, limit=limit)
    return [a["title"] for a in articles]


def fetch_structured_news(symbol: str, limit: int = 8) -> List[Dict[str, Any]]:
    """Fetch rich financial news headlines with source and link from Google News RSS or NewsAPI."""
    clean_sym = symbol.replace('-USD', '').replace('.NS', '').replace('.BO', '')
    query = clean_sym
    if symbol.endswith('-USD'):
        query = f"{clean_sym} crypto"
    elif '.NS' in symbol or '.BO' in symbol:
        query = f"{clean_sym} share price stock"
    else:
        query = f"{clean_sym} stock market"

    items = []
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
        
        root = ET.fromstring(xml_data)
        for item_node in root.findall(".//item")[:limit]:
            title = item_node.findtext("title") or "Market Update"
            pub_date = item_node.findtext("pubDate") or "Recent"
            source = item_node.findtext("source") or "Financial Wire"
            link = item_node.findtext("link") or "#"
            
            sc = score_text(title)
            sentiment_tag = "BULLISH" if sc >= 0.15 else ("BEARISH" if sc <= -0.15 else "NEUTRAL")
            
            items.append({
                "title": title,
                "source": source,
                "pub_date": pub_date,
                "link": link,
                "score": round(sc, 3),
                "sentiment": sentiment_tag
            })
    except Exception:
        pass

    return items


def compute_sentiment_score(headlines: List[str]) -> float:
    """Compute aggregate sentiment score across headlines between -1.0 and 1.0."""
    if not headlines:
        return 0.0
    scores = [score_text(h) for h in headlines]
    return round(sum(scores) / len(scores), 3)


def get_sentiment_score(symbol: str) -> float:
    """High-level helper: fetch headlines and return sentiment score."""
    headlines = fetch_news_headlines(symbol)
    return compute_sentiment_score(headlines)

