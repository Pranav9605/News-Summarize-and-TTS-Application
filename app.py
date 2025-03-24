import streamlit as st
import pandas as pd
import json
import requests

# Base URL for the FastAPI backend
BACKEND_BASE_URL = "https://pranav9605-test2.hf.space"

def fetch_company_news(company_name: str):
    """
    Calls the backend /api/sentiment endpoint to get news analysis.
    """
    url = f"{BACKEND_BASE_URL}/api/sentiment"
    payload = {"company_name": company_name}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            return f"Error: {data.get('detail', 'Unknown error')}"
        return data["data"]
    except Exception as e:
        return f"Error: {str(e)}"

def get_text_to_speech(text: str, lang: str = "hi"):
    """
    Calls the backend /api/tts endpoint to convert text to speech.
    """
    url = f"{BACKEND_BASE_URL}/api/tts"
    params = {"text": text, "lang": lang}
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            return None
        return data["audio_file"]
    except Exception as e:
        return None

def main():
    st.title("News Summarization and Sentiment Analysis")
    st.write("Enter a company name to get news, sentiment analysis, and an audio summary in Hindi.")
    
    # Company input options
    company_options = ["Zomato", "Swiggy", "Bigbasket", "Tesla", "Tata", "Reliance", "Infosys", "TCS"]
    company_name = st.selectbox("Select a company", company_options)
    custom_company = st.text_input("Or enter a custom company name")
    
    if custom_company:
        company_name = custom_company
    
    if st.button("Analyze News"):
        with st.spinner(f"Fetching and analyzing news for {company_name}..."):
            news_data = fetch_company_news(company_name)
            if isinstance(news_data, str):
                st.error(news_data)
            else:
                display_results(news_data, company_name)

def display_results(news_data, company_name):
    st.subheader(f"News Analysis for {company_name}")
    
    df = pd.DataFrame([{
        "Title": article["title"],
        "Summary": article["summary"],
        "Sentiment": f"{article['sentiment']['label']} ({article['sentiment']['score']})",
        "Topics": ", ".join(article.get("topics", ["General"]))
    } for article in news_data["Articles"]])
    st.dataframe(df)
    
    # Display sentiment distribution
    st.subheader("Sentiment Distribution")
    dist = news_data["Comparative Sentiment Score"]["Sentiment Distribution"]
    sentiment_df = pd.DataFrame({
        "Sentiment": ["Positive", "Negative", "Neutral"],
        "Count": [dist["Positive"], dist["Negative"], dist["Neutral"]]
    })
    st.bar_chart(sentiment_df.set_index("Sentiment"))
    
    # Display comparative analysis
    st.subheader("Comparative Analysis")
    for comparison in news_data["Comparative Sentiment Score"]["Coverage Differences"]:
        st.write(f"**Comparison:** {comparison['Comparison']}")
        st.write(f"**Impact:** {comparison['Impact']}")
        st.write("---")
    
    # Display topic overlap
    st.subheader("Topic Analysis")
    topic_overlap = news_data["Comparative Sentiment Score"]["Topic Overlap"]
    st.write(f"**Common Topics:** {', '.join(topic_overlap['Common Topics'])}")
    
    # Display final sentiment analysis
    st.subheader("Final Sentiment Analysis")
    st.write(news_data["Final Sentiment Analysis"])
    
    # Display audio summary in Hindi
    st.subheader("Audio Summary (Hindi)")
    audio_file = get_text_to_speech(news_data["Final Sentiment Analysis"], lang="hi")
    if audio_file:
        st.audio(audio_file, format='audio/mp3')
    else:
        st.write("Audio not available.")
    
    # Option to view raw JSON data
    with st.expander("View Raw JSON"):
        st.json(news_data)

if __name__ == "__main__":
    main()
