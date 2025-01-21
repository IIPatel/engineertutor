import streamlit as st
import requests
from typing import Dict, Optional
import time
from datetime import datetime
import json
import os

class APIHandler:
    def __init__(self, api_key: str):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.base_urls = {
            "chat": "https://api.electronhub.top/chat/completions",
            "audio": "https://api.electronhub.top/audio/speech",
            "image": "https://api.electronhub.top/images/generations"
        }
        
    def make_request(self, endpoint: str, payload: Dict) -> Optional[requests.Response]:
        try:
            response = requests.post(
                self.base_urls[endpoint],
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return None

class Cache:
    def __init__(self):
        self.cache_file = "response_cache.json"
        self.cache = self.load_cache()
        
    def load_cache(self) -> Dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
            
    def get_cached_response(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            # Check if cache is less than 24 hours old
            timestamp = self.cache[key]["timestamp"]
            if time.time() - timestamp < 86400:  # 24 hours
                return self.cache[key]["data"]
        return None
    
    def cache_response(self, key: str, data: Dict):
        self.cache[key] = {
            "timestamp": time.time(),
            "data": data
        }
        self.save_cache()

class EngineeringTutor:
    def __init__(self):
        self.setup_streamlit()
        self.api = APIHandler(st.secrets["API_KEY"])
        self.cache = Cache()
        
    def setup_streamlit(self):
        st.set_page_config(
            page_title="AI Engineering Tutor",
            page_icon="🎓",
            layout="wide"
        )
        st.title("🎓 AI Engineering Tutor")
        st.subheader("Master engineering concepts with interactive AI assistance!")
        
        # Add sidebar for settings and information
        with st.sidebar:
            st.markdown("### About")
            st.info(
                "This app uses AI to explain engineering concepts through "
                "text, audio, and visual representations."
            )
            st.markdown("### Settings")
            st.session_state.difficulty = st.select_slider(
                "Explanation Difficulty",
                options=["Beginner", "Intermediate", "Advanced"]
            )
            
    def get_explanation_prompt(self, topic: str) -> str:
        difficulty_prompts = {
            "Beginner": "Explain {topic} in simple terms, using everyday examples.",
            "Intermediate": "Explain {topic} with technical details and practical applications.",
            "Advanced": "Provide an in-depth explanation of {topic} with mathematical formulas and advanced concepts."
        }
        return difficulty_prompts[st.session_state.difficulty].format(topic=topic)
    
    def generate_text_explanation(self, topic: str) -> Optional[str]:
        cache_key = f"text_{topic}_{st.session_state.difficulty}"
        cached_response = self.cache.get_cached_response(cache_key)
        
        if cached_response:
            return cached_response
            
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": self.get_explanation_prompt(topic)}]
        }
        
        response = self.api.make_request("chat", payload)
        if response:
            explanation = response.json()["choices"][0]["message"]["content"]
            self.cache.cache_response(cache_key, explanation)
            return explanation
        return None
    
    def generate_audio_explanation(self, topic: str) -> Optional[str]:
        cache_key = f"audio_{topic}_{st.session_state.difficulty}"
        cached_response = self.cache.get_cached_response(cache_key)
        
        if cached_response:
            return cached_response
            
        payload = {
            "text": self.get_explanation_prompt(topic),
            "voice": "en-US-Wavenet-D"
        }
        
        response = self.api.make_request("audio", payload)
        if response:
            audio_url = response.json()["url"]
            self.cache.cache_response(cache_key, audio_url)
            return audio_url
        return None
    
    def generate_image_visualization(self, topic: str) -> Optional[str]:
        cache_key = f"image_{topic}_{st.session_state.difficulty}"
        cached_response = self.cache.get_cached_response(cache_key)
        
        if cached_response:
            return cached_response
            
        payload = {
            "prompt": f"Technical diagram or visualization of {topic} in engineering context"
        }
        
        response = self.api.make_request("image", payload)
        if response:
            image_url = response.json()["data"][0]["url"]
            self.cache.cache_response(cache_key, image_url)
            return image_url
        return None
    
    def run(self):
        # Create two columns for input
        col1, col2 = st.columns(2)
        
        with col1:
            topic = st.text_input(
                "Enter an engineering topic:",
                placeholder="e.g., Bernoulli's Principle, Fluid Mechanics"
            )
            
        with col2:
            output_type = st.multiselect(
                "Select output formats:",
                ["Text", "Audio", "Image"],
                default=["Text"]
            )
            
        if st.button("Generate Explanation", type="primary"):
            if not topic:
                st.error("Please enter a topic.")
                return
                
            with st.spinner("Generating response..."):
                # Create tabs for different output formats
                if output_type:
                    tabs = st.tabs(output_type)
                    
                    for tab, format_type in zip(tabs, output_type):
                        with tab:
                            if format_type == "Text":
                                explanation = self.generate_text_explanation(topic)
                                if explanation:
                                    st.markdown(explanation)
                                    
                            elif format_type == "Audio":
                                audio_url = self.generate_audio_explanation(topic)
                                if audio_url:
                                    st.audio(audio_url)
                                    
                            elif format_type == "Image":
                                image_url = self.generate_image_visualization(topic)
                                if image_url:
                                    st.image(image_url, caption=f"Visualization of {topic}")
                                    
        # Add footer with timestamp
        st.markdown("---")
        st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    tutor = EngineeringTutor()
    tutor.run()