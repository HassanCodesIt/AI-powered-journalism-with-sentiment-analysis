from fastapi import FastAPI, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from newspaper import Article
import feedparser
from sentiment import analyze_sentiment
from dotenv import load_dotenv
import os


load_dotenv()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return FileResponse("templates/news.html")


@app.get("/chat-page")
def chat_page():
    return FileResponse("templates/chat.html")


@app.get("/scrap")
def scraping():
    feed_urls = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "http://rss.cnn.com/rss/edition_world.rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.theguardian.com/world/rss"
    ]
    
    articles = []

    for url in feed_urls:
        feed = feedparser.parse(url)
        # Limit to 5 articles per source for performance
        for entry in feed.entries[:5]: 
            try:
                article = Article(
                    entry.link,
                    browser_user_agent="Mozilla/5.0"
                )
                article.download()
                article.parse()

                # skip empty content
                if not article.text or not article.text.strip():
                    continue

                # sentiment (safe)
                try:
                    sentiment = analyze_sentiment(article.text)
                    label = sentiment.get("label", "neutral")
                    score = sentiment.get("score", 0.0)
                except:
                    label = "neutral"
                    score = 0.0

                articles.append({
                    "title": article.title or "No title",
                    "text": article.text,
                    "sentiment": label,
                    "score": score,
                    "length": len(article.text)
                })

            except Exception as e:
                # skip broken articles
                print(f"Skipped article from {url}: {entry.link}")
                continue

    # Sort articles by length in descending order (longer news at the top)
    articles.sort(key=lambda x: x["length"], reverse=True)

    return articles



@app.post("/summarize")
def summarize(article_text: str = Form(...)):
    client = Groq(api_key=os.getenv("API_KEY"))

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": (
                    "Summarize the following news article into 3 bullet points.\n"
                    "Use plain text with * bullets.\n\n"
                    f"{article_text}"
                )
            }
        ],
        stream=True
    )

    summary = ""
    for chunk in completion:
        summary += chunk.choices[0].delta.content or ""

    return {"summary": summary}


@app.post("/chat")
def chat_with_article(
    article_text: str = Form(...),
    question: str = Form(...)
):
    client = Groq(api_key=os.getenv("API_KEY"))

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": (
                    f"Based on this article:\n{article_text}\n\n"
                    f"Answer this question:\n{question}"
                )
            }
        ],
        stream=True
    )

    answer = ""
    for chunk in completion:
        answer += chunk.choices[0].delta.content or ""

    return {"answer": answer}


@app.post("/user-news")
def user_news(news_url: str = Form(...)):
    try:
        article = Article(news_url, browser_user_agent="Mozilla/5.0")
        article.download()
        article.parse()
        return {"text": article.text}
    except Exception as e:
        return {"error": str(e)}
