import requests
from bs4 import BeautifulSoup
# tried sentiment analysis implementation using TextBlob
# vader is working better (commented out):
# from textblob import TextBlob

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import Counter
from googletrans import Translator
from gtts import gTTS
import tempfile
import os
import string
import itertools
import numpy as np
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
nltk.download('punkt_tab')
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    pass  # Handle offline case

# Import VADER for sentiment analysis
from nltk.sentiment.vader import SentimentIntensityAnalyzer
vader_analyzer = SentimentIntensityAnalyzer()

def get_news(company_name):

    rss_url = f"https://news.google.com/rss/search?q={company_name}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(rss_url, headers=headers)
        
        if response.status_code != 200:
            return f"Failed to fetch news. Status code: {response.status_code}"
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        
        articles = soup.find_all("item")[:10]  # Get 10 articles
        
        if not articles:
            return f"No news found for {company_name}"
        
        news_list = []
        for article in articles:
            title_elem = article.find("title")
            link_elem = article.find("link")
            
            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem.text.strip()
                
                news_list.append({"title": title, "url": link})
        
        return news_list
    
    except Exception as e:
        return f"Error fetching news: {str(e)}"

def summarize_article(text, max_words=50):

    if len(text.split()) <= max_words:
        return text
    
    # Simple extractive summarization
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if len(sentences) <= 1:
        words = text.split()
        return " ".join(words[:max_words]) + "..."
        
    # Score sentences by position (first sentences often contain key info)
    scored_sentences = [(i, sent) for i, sent in enumerate(sentences)]
    sorted_sentences = sorted(scored_sentences, key=lambda x: x[0])
    
    # Take top sentences until we hit max words
    summary = []
    word_count = 0
    
    for _, sentence in sorted_sentences:
        words_in_sentence = len(sentence.split())
        if word_count + words_in_sentence <= max_words:
            summary.append(sentence)
            word_count += words_in_sentence
        else:
            break
    
    # If we don't have any sentences yet, just take the first part
    if not summary and text:
        words = text.split()
        return " ".join(words[:max_words]) + "..."
    
    return " ".join(summary)

def analyze_sentiment(text):

    # Previous implementation using TextBlob 
    """
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"
    return {
        "score": round(polarity, 2),
        "label": label
    }
    """
    # New implementation using VADER
    scores = vader_analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"
    return {
        "score": round(compound, 2),
        "label": label,
        "detailed": scores
    }

def extract_topics(text, num_topics=3):

    # Preprocessing
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    try:
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word not in stop_words]
    except:
        # Fallback if NLTK data not available
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with"}
        tokens = [word for word in tokens if word not in common_words]
    
    # Remove single characters
    tokens = [word for word in tokens if len(word) > 1]
    
    # Lemmatize
    try:
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
    except:
        pass  # Skip lemmatization if not available
    
    # Get most common words as topics
    word_counts = Counter(tokens)
    topics = [word for word, _ in word_counts.most_common(num_topics)]
    
    # If we found fewer topics than requested, add some generic ones
    default_topics = ["News", "Business", "Finance", "Technology", "Market", "Products"]
    while len(topics) < num_topics and default_topics:
        topics.append(default_topics.pop(0))
        
    return topics[:num_topics]

def perform_comparative_analysis(articles):

    # Count sentiments
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for article in articles:
        sentiment = article["sentiment"]["label"]
        sentiment_counts[sentiment] += 1
    
    # Collect all topics
    all_topics = []
    for article in articles:
        all_topics.extend(article["topics"])
    
    # Find common topics
    topic_counts = Counter(all_topics)
    common_topics = [topic for topic, count in topic_counts.items() if count > 1]
    
    # Generate comparisons
    comparisons = []
    
    # Compare sentiment differences
    pos_articles = [a for a in articles if a["sentiment"]["label"] == "positive"]
    neg_articles = [a for a in articles if a["sentiment"]["label"] == "negative"]
    
    if pos_articles and neg_articles:
        pos_title = pos_articles[0]["title"]
        neg_title = neg_articles[0]["title"]
        
        comparison = {
            "Comparison": f"Some articles like '{pos_title[:30]}...' are positive, while others like '{neg_title[:30]}...' are negative.",
            "Impact": "This mixed sentiment suggests varied market perception which might lead to stock volatility."
        }
        comparisons.append(comparison)
    
    # Topic-based comparison
    if len(articles) >= 2:
        article1 = articles[0]
        article2 = articles[1]
        
        unique_topics1 = [t for t in article1["topics"] if t not in article2["topics"]]
        unique_topics2 = [t for t in article2["topics"] if t not in article1["topics"]]
        
        if unique_topics1 and unique_topics2:
            comparison = {
                "Comparison": f"Article 1 focuses on {', '.join(unique_topics1)}, while Article 2 discusses {', '.join(unique_topics2)}.",
                "Impact": "The diverse coverage indicates the company is active in multiple domains."
            }
            comparisons.append(comparison)
    
    # If we don't have enough comparisons, add a generic one
    if len(comparisons) < 2:
        if sentiment_counts["positive"] > sentiment_counts["negative"]:
            comparison = {
                "Comparison": "Most articles have a positive sentiment toward the company.",
                "Impact": "This positive coverage may indicate strong market performance or successful recent initiatives."
            }
        elif sentiment_counts["negative"] > sentiment_counts["positive"]:
            comparison = {
                "Comparison": "Most articles have a negative sentiment toward the company.",
                "Impact": "This negative coverage may indicate challenges or issues the company is facing."
            }
        else:
            comparison = {
                "Comparison": "Articles show a mix of sentiments without a clear trend.",
                "Impact": "The balanced coverage suggests the company is in a transitional or stable phase."
            }
        comparisons.append(comparison)
    
    # Find unique topics in each article
    unique_topics = {}
    for i, article in enumerate(articles[:5]):  # Limit to first 5 articles
        article_topics = set(article["topics"])
        other_topics = set(itertools.chain.from_iterable([a["topics"] for j, a in enumerate(articles) if j != i]))
        unique_topics[f"Unique Topics in Article {i+1}"] = list(article_topics - other_topics)
    
    # Remove empty lists
    unique_topics = {k: v for k, v in unique_topics.items() if v}
    
    # Create response
    result = {
        "Sentiment Distribution": {
            "Positive": sentiment_counts["positive"],
            "Negative": sentiment_counts["negative"],
            "Neutral": sentiment_counts["neutral"]
        },
        "Coverage Differences": comparisons,
        "Topic Overlap": {
            "Common Topics": common_topics if common_topics else ["General Business News"],
            **unique_topics
        }
    }
    
    return result

def generate_hindi_tts(text, lang="hi"):

    try:
        # If text is in English, translate to Hindi
        if detect_language(text) != "hi":
            translator = Translator()
            text = translator.translate(text, dest=lang).text
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        # Generate TTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_filename)
        
        return temp_filename
    except Exception as e:
        # Fallback to a simple message if TTS fails
        print(f"TTS Error: {str(e)}")
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_filename = temp_file.name
        temp_file.close()
        
        fallback_text = "नमस्ते, यह एक परीक्षण संदेश है।"  # "Hello, this is a test message" in Hindi
        tts = gTTS(text=fallback_text, lang=lang, slow=False)
        tts.save(temp_filename)
        
        return temp_filename

def detect_language(text):

    try:
        translator = Translator()
        return translator.detect(text).lang
    except:
        return "en"  # Default to English if detection fails
