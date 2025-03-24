import streamlit as st
import requests
import json

# Backend URL
BACKEND_URL = "https://pranav9605-test2.hf.space"

def fetch_news(company_name):
    """Fetch news summaries from the backend."""
    url = f"{BACKEND_URL}/api/news"
    params = {"company": company_name}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return None

def get_text_to_speech(text, lang="hi"):
    """Fetch Hindi text-to-speech audio from the backend."""
    url = f"{BACKEND_URL}/api/tts"
    params = {"text": text, "lang": lang}
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "success":
            st.error("TTS conversion failed.")
            return None
        
        audio_file = data.get("audio_file")
        st.write(f"DEBUG: Received audio file: {audio_file}")  # Debugging statement
        
        if audio_file.startswith("http"):
            return audio_file  # If it's a URL, return it directly
        else:
            try:
                with open(audio_file, "rb") as f:
                    return f.read()  # Return binary data if it's a local file
            except Exception as e:
                st.error(f"Error reading local audio file: {e}")
                return None
    except requests.exceptions.RequestException as e:
        st.error(f"TTS request error: {e}")
        return None

def display_results(news_data, company_name):
    """Display news summaries and TTS audio."""
    if not news_data or "summaries" not in news_data:
        st.warning("No news data available.")
        return
    
    st.header(f"News Summary for {company_name}")
    for idx, summary in enumerate(news_data["summaries"], start=1):
        st.subheader(f"News {idx}")
        st.write(summary)
        
        # Get TTS audio
        audio_data = get_text_to_speech(summary, lang="hi")
        if audio_data:
            if isinstance(audio_data, str):
                st.audio(audio_data, format="audio/mp3")  # URL
            else:
                st.audio(audio_data, format="audio/mp3", start_time=0)  # Binary data

def main():
    """Main Streamlit app UI."""
    st.title("News Summarization and Text-to-Speech Application")
    company_name = st.text_input("Enter Company Name:")
    if st.button("Analyze News"):
        if company_name:
            news_data = fetch_news(company_name)
            display_results(news_data, company_name)
        else:
            st.warning("Please enter a company name.")

if __name__ == "__main__":
    main()
