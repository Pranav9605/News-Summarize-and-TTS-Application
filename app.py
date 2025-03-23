# app.py
import streamlit as st
import pandas as pd
import json
from api import fetch_company_news, get_sentiment_analysis, get_text_to_speech


def main():
    st.title("News Summarization and Sentiment Analysis")
    st.write("Enter a company name to get news, sentiment analysis, and audio summary in Hindi")
    
    # Company input
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
    
    # Display sentiment 
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
    
    # Display final sentiment
    st.subheader("Final Sentiment Analysis")
    st.write(news_data["Final Sentiment Analysis"])
    
    # Display audio
    st.subheader("Audio Summary (Hindi)")
    audio_file = get_text_to_speech(news_data["Final Sentiment Analysis"], lang="hi")
    st.audio(audio_file, format='audio/mp3')
    
    # Display raw JSON
    with st.expander("View Raw JSON"):
        st.json(news_data)

if __name__ == "__main__":
    main()