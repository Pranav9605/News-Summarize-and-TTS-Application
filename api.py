# api.py
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from utils import get_news, analyze_sentiment, summarize_article, extract_topics, perform_comparative_analysis, generate_hindi_tts
import tempfile
import os

app = FastAPI()

class CompanyRequest(BaseModel):
    company_name: str

@app.post("/api/news")
def api_fetch_news(request: CompanyRequest):
    """API endpoint to fetch news for a company"""
    try:
        news_list = get_news(request.company_name)
        if isinstance(news_list, str):
            raise HTTPException(status_code=404, detail=news_list)
        return {"status": "success", "data": news_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sentiment")
def api_analyze_sentiment(request: CompanyRequest):
    """API endpoint to get full sentiment analysis"""
    try:
        news_list = get_news(request.company_name)
        if isinstance(news_list, str):
            raise HTTPException(status_code=404, detail=news_list)
            
        # Process each news article
        articles = []
        for news in news_list:
            summary = summarize_article(news["title"])
            sentiment = analyze_sentiment(summary)
            topics = extract_topics(summary)
            
            articles.append({
                "title": news["title"],
                "url": news["url"],
                "summary": summary,
                "sentiment": sentiment,
                "topics": topics
            })
            
        # Perform comparative analysis
        comparative = perform_comparative_analysis(articles)
        
        # Generate final sentiment analysis
        positive_count = comparative["Sentiment Distribution"]["Positive"]
        negative_count = comparative["Sentiment Distribution"]["Negative"]
        total = positive_count + negative_count + comparative["Sentiment Distribution"]["Neutral"]
        
        if positive_count > negative_count:
            final_sentiment = f"{request.company_name}'s latest news coverage is mostly positive. Potential stock growth expected."
        elif negative_count > positive_count:
            final_sentiment = f"{request.company_name}'s latest news coverage is mostly negative. Caution advised for investors."
        else:
            final_sentiment = f"{request.company_name}'s latest news coverage is mixed or neutral. Market reaction may vary."
        
        # Prepare response
        response = {
            "Company": request.company_name,
            "Articles": articles,
            "Comparative Sentiment Score": comparative,
            "Final Sentiment Analysis": final_sentiment
        }
        
        return {"status": "success", "data": response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
def api_text_to_speech(text: str, lang: str = "hi"):
    """API endpoint to convert text to speech"""
    try:
        audio_file = generate_hindi_tts(text)
        return {"status": "success", "audio_file": audio_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_company_news(company_name):
    """Client function to fetch news analysis"""
    try:

        news_list = get_news(company_name)
        if isinstance(news_list, str):
            return news_list
            

        articles = []
        for news in news_list:
            summary = summarize_article(news["title"])
            sentiment = analyze_sentiment(summary)
            topics = extract_topics(summary)
            
            articles.append({
                "title": news["title"],
                "url": news["url"],
                "summary": summary,
                "sentiment": sentiment,
                "topics": topics
            })
            
        # Perform comparative analysis
        comparative = perform_comparative_analysis(articles)
        
        # Generate final sentiment analysis
        positive_count = comparative["Sentiment Distribution"]["Positive"]
        negative_count = comparative["Sentiment Distribution"]["Negative"]
        total = positive_count + negative_count + comparative["Sentiment Distribution"]["Neutral"]
        
        if positive_count > negative_count:
            final_sentiment = f"{company_name}'s latest news coverage is mostly positive. Potential stock growth expected."
        elif negative_count > positive_count:
            final_sentiment = f"{company_name}'s latest news coverage is mostly negative. Caution advised for investors."
        else:
            final_sentiment = f"{company_name}'s latest news coverage is mixed or neutral. Market reaction may vary."
        
        # Prepare response
        response = {
            "Company": company_name,
            "Articles": articles,
            "Comparative Sentiment Score": comparative,
            "Final Sentiment Analysis": final_sentiment
        }
        
        return response
        
    except Exception as e:
        return f"Error: {str(e)}"

def get_sentiment_analysis(text):
    """Client function to get sentiment"""
    return analyze_sentiment(text)

def get_text_to_speech(text, lang="hi"):
    """Client function to get TTS audio"""
    return generate_hindi_tts(text)