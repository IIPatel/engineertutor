import streamlit as st
import requests
import base64
from pathlib import Path
import tempfile
import orjson
from typing import Generator, Dict, Any, Optional, List
import json
from datetime import datetime
import io
from PIL import Image

class EnhancedAPIClient:
    """Enhanced API client supporting streaming and multimedia"""
    
    def __init__(self):
        self.base_url = "https://api.electronhub.top"
        self.api_key = st.secrets["API_KEY"]
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
        
    def stream_completion(
        self, 
        messages: List[Dict], 
        model: str = "gpt-4",
        max_tokens: Optional[int] = None,
        include_usage: bool = False
    ) -> Generator[str, None, None]:
        """Stream completion responses"""
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": include_usage}
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        with requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            stream=True
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    if "choices" in chunk:
                        yield chunk["choices"][0]["delta"].get("content", "")

    def analyze_image(self, image: bytes, prompt: str) -> str:
        """Analyze image using vision model"""
        base64_image = base64.b64encode(image).decode('utf-8')
        
        payload = {
            "model": "gpt-4o",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate_speech(self, text: str) -> bytes:
        """Generate speech from text"""
        payload = {
            "model": "eleven-multilingual-v2",
            "voice": "nova",
            "input": text
        }
        
        response = requests.post(
            f"{self.base_url}/audio/speech",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.content

    def generate_video(self, prompt: str) -> str:
        """Generate video from prompt"""
        payload = {
            "model": "t2v-turbo",
            "prompt": prompt
        }
        
        with requests.post(
            f"{self.base_url}/videos/generations",
            headers=self.headers,
            json=payload,
            stream=True
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = orjson.loads(line)
                    if "data" in data:
                        return data["data"][0]["url"]
            return ""

class EngineeringTutor:
    """Enhanced Engineering Tutor with multimedia capabilities"""
    
    def __init__(self):
        self.api = EnhancedAPIClient()
        self.initialize_session_state()
        self.setup_ui()
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'history' not in st.session_state:
            st.session_state.history = []
        if 'current_explanation' not in st.session_state:
            st.session_state.current_explanation = ""
            
    def setup_ui(self):
        """Setup the Streamlit UI"""
        st.set_page_config(
            page_title="Engineering Learning Hub",
            page_icon="🎓",
            layout="wide"
        )
        
        st.markdown("""
            <style>
                .stApp { max-width: 1200px; margin: 0 auto; }
                .explanation-container { height: 400px; overflow-y: auto; }
                .multimedia-container { padding: 10px; border: 1px solid #ddd; }
            </style>
        """, unsafe_allow_html=True)
        
    def run(self):
        """Run the main application"""
        st.title("🎓 Advanced Engineering Learning Hub")
        
        # Sidebar settings
        with st.sidebar:
            st.title("⚙️ Settings")
            model = st.selectbox(
                "Select Model",
                ["gpt-4", "gpt-3.5-turbo", "gemma-7b"]
            )
            depth = st.select_slider(
                "Learning Depth",
                options=["Beginner", "Intermediate", "Advanced"]
            )
            
            st.title("📚 Learning Tools")
            tool_type = st.radio(
                "Select Learning Mode",
                ["Text", "Image Analysis", "Interactive", "Video"]
            )
        
        # Main content area
        if tool_type == "Text":
            self.render_text_mode(model, depth)
        elif tool_type == "Image Analysis":
            self.render_image_mode()
        elif tool_type == "Interactive":
            self.render_interactive_mode(model)
        elif tool_type == "Video":
            self.render_video_mode()
            
    def render_text_mode(self, model: str, depth: str):
        """Render text-based learning mode"""
        topic = st.text_input("Enter engineering topic:")
        
        if st.button("Start Learning", type="primary"):
            if not topic:
                st.error("Please enter a topic!")
                return
                
            messages = [
                {
                    "role": "system",
                    "content": f"You are an engineering tutor explaining at {depth} level."
                },
                {
                    "role": "user",
                    "content": f"Explain {topic} with examples and applications."
                }
            ]
            
            # Create placeholder for streaming text
            explanation_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for chunk in self.api.stream_completion(messages, model):
                full_response += chunk
                explanation_placeholder.markdown(full_response + "▌")
            explanation_placeholder.markdown(full_response)
            
            # Generate audio version
            if st.button("🔊 Listen to Explanation"):
                with st.spinner("Generating audio..."):
                    audio_data = self.api.generate_speech(full_response)
                    st.audio(audio_data)
                    
    def render_image_mode(self):
        """Render image analysis mode"""
        uploaded_file = st.file_uploader(
            "Upload an engineering diagram or schema",
            type=["png", "jpg", "jpeg"]
        )
        
        if uploaded_file:
            image_bytes = uploaded_file.getvalue()
            st.image(image_bytes, caption="Uploaded Image")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Analyze Diagram"):
                    with st.spinner("Analyzing..."):
                        analysis = self.api.analyze_image(
                            image_bytes,
                            "Explain this engineering diagram in detail."
                        )
                        st.markdown(analysis)
            
            with col2:
                if st.button("Identify Components"):
                    with st.spinner("Identifying..."):
                        components = self.api.analyze_image(
                            image_bytes,
                            "List and explain each component in this diagram."
                        )
                        st.markdown(components)
                        
    def render_interactive_mode(self, model: str):
        """Render interactive learning mode"""
        st.subheader("Interactive Learning Session")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": "You are an interactive engineering tutor."
                }
            ]
        
        for message in st.session_state.messages[1:]:  # Skip system message
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        prompt = st.chat_input("Ask your engineering question")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                for chunk in self.api.stream_completion(
                    st.session_state.messages,
                    model
                ):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )
            
    def render_video_mode(self):
        """Render video-based learning mode"""
        st.subheader("Video Visualization")
        
        topic = st.text_input(
            "Enter engineering concept for visualization:",
            placeholder="e.g., How a four-stroke engine works"
        )
        
        if st.button("Generate Video"):
            if not topic:
                st.error("Please enter a topic!")
                return
                
            with st.spinner("Generating video visualization..."):
                try:
                    video_url = self.api.generate_video(
                        f"Technical visualization of {topic}"
                    )
                    if video_url:
                        st.video(video_url)
                    else:
                        st.error("Video generation failed. Please try again.")
                except Exception as e:
                    st.error(f"Error generating video: {str(e)}")

if __name__ == "__main__":
    tutor = EngineeringTutor()
    tutor.run()