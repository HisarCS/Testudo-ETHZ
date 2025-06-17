import requests
import json
import asyncio
import edge_tts
import time
import re
import os
from typing import Optional, Dict, Any
from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta

class TestudoAI:
    def __init__(self, 
                 lm_studio_url: str = "http://localhost:1234",
                 model_name: str = "emotion-llama",
                 voice: str = "en-US-JennyNeural",
                 user_data_file: str = "user_data.json"):
        self.lm_studio_url = lm_studio_url
        self.model_name = model_name
        self.voice = voice
        self.conversation_history = []
        self.user_data_file = user_data_file
        self.user_data = self.load_user_data()
        self.system_prompt = "You are Testudo, an ai enabled pet like companion. Designed as an turtle. Reply in 1–2 short natural sentences. Avoid emoticons or roleplay stage directions. Don't call people 'friend', 'creator', or other names unless you know their actual name from the conversation. Never use asterisks for actions or movements."
    
    def load_user_data(self) -> Dict[str, Any]:
        """Load user data from JSON file"""
        try:
            if os.path.exists(self.user_data_file):
                with open(self.user_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Loaded user data: {list(data.keys())}")
                    return data
            else:
                print("No user data file found, creating new one")
                return {}
        except Exception as e:
            print(f" Error loading user data: {e}")
            return {}
    
    def save_user_data(self):
        """Save user data to JSON file"""
        try:
            with open(self.user_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, indent=2, ensure_ascii=False)
            print(f"User data saved to {self.user_data_file}")
        except Exception as e:
            print(f" Error saving user data: {e}")
    
    def extract_personal_info(self, message: str) -> Dict[str, Any]:
        """Extract personal information from user message"""
        extracted = {}
        message_lower = message.lower().strip()
        

        name_patterns = [
            r"my name is ([a-zA-Z\s]+)",
            r"i'm ([a-zA-Z\s]+)",
            r"i am ([a-zA-Z\s]+)",
            r"call me ([a-zA-Z\s]+)",
            r"i'm called ([a-zA-Z\s]+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                name = match.group(1).strip().title()

                common_words = ['happy', 'sad', 'tired', 'good', 'fine', 'okay', 'great', 'studying', 'working', 'here', 'back', 'done']
                if name.lower() not in common_words and len(name) > 1:
                    extracted['name'] = name
                    break
        
 
        age_patterns = [
            r"i am (\d+) years old",
            r"i'm (\d+) years old",
            r"i am (\d+)",
            r"i'm (\d+)",
            r"(\d+) years old"
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                if 1 <= age <= 120: 
                    extracted['age'] = age
                    break
        
        location_patterns = [
            r"i live in ([a-zA-Z\s]+)",
            r"i'm from ([a-zA-Z\s]+)",
            r"i am from ([a-zA-Z\s]+)",
            r"i'm in ([a-zA-Z\s]+)",
            r"i am in ([a-zA-Z\s]+)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message_lower)
            if match:
                location = match.group(1).strip().title()
                if len(location) > 1:
                    extracted['location'] = location
                    break
        

        job_patterns = [
            r"i work as a ([a-zA-Z\s]+)",
            r"i work as an ([a-zA-Z\s]+)",
            r"i am a ([a-zA-Z\s]+)",
            r"i'm a ([a-zA-Z\s]+)",
            r"my job is ([a-zA-Z\s]+)"
        ]
        
        for pattern in job_patterns:
            match = re.search(pattern, message_lower)
            if match:
                job = match.group(1).strip().title()

                job_words = ['student', 'teacher', 'doctor', 'engineer', 'programmer', 'developer', 'designer', 'writer', 'artist', 'lawyer', 'nurse', 'manager']
                if any(word in job.lower() for word in job_words) or len(job.split()) <= 3:
                    extracted['occupation'] = job
                    break
        
        return extracted
    
    def update_user_data(self, new_data: Dict[str, Any]):
        """Update user data with new information"""
        updated = False
        for key, value in new_data.items():
            if key not in self.user_data or self.user_data[key] != value:
                self.user_data[key] = value
                updated = True
                print(f"Updated {key}: {value}")
        
        if updated:
            self.save_user_data()
        
        return updated
    
    def get_user_context(self) -> str:
        """Get user context for AI responses"""
        if not self.user_data:
            return ""
        
        context_parts = []
        if 'name' in self.user_data:
            context_parts.append(f"User's name is {self.user_data['name']}")
        if 'age' in self.user_data:
            context_parts.append(f"{self.user_data['age']} years old")
        if 'location' in self.user_data:
            context_parts.append(f"lives in {self.user_data['location']}")
        if 'occupation' in self.user_data:
            context_parts.append(f"works as {self.user_data['occupation']}")
        
        if context_parts:
            return f"Personal info about user: {', '.join(context_parts)}. "
        return ""
        """Get current date and time in Istanbul (UTC+3)"""
        istanbul_tz = timezone(timedelta(hours=3))
        now = datetime.now(istanbul_tz)
        return now.strftime("%Y-%m-%d %H:%M")
    
    def get_istanbul_time_detailed(self) -> str:
        """Get detailed current date and time in Istanbul"""
        istanbul_tz = timezone(timedelta(hours=3))
        now = datetime.now(istanbul_tz)
        return now.strftime("%A, %B %d, %Y at %H:%M (Istanbul time)")
    
    def filter_asterisk_actions(self, text: str) -> str:
        """Remove text within asterisks (movement/action descriptions)"""
        if not text:
            return text
        

        filtered_text = re.sub(r'\*[^*]*\*', '', text)
        
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        return filtered_text
    
    def needs_time_info(self, prompt: str) -> bool:
        """Check if the question is asking for time/date information"""
        time_keywords = [
            "what time", "what's the time", "current time", "time is it",
            "what date", "what's the date", "current date", "date today",
            "today", "now", "current", "when is it"
        ]
        
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in time_keywords)
    def check_connection(self) -> bool:
        """Check if LM Studio is running"""
        try:
            response = requests.get(f"{self.lm_studio_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models = response.json()
                available_models = [model["id"] for model in models.get("data", [])]
                print(f" LM Studio connected. Models: {available_models}")
                
                if self.model_name not in available_models and available_models:
                    self.model_name = available_models[0]
                    print(f"Using model: {self.model_name}")
                
                return True
            else:
                print(f" LM Studio error: {response.status_code}")
                return False
        except Exception as e:
            print(f" Cannot connect to LM Studio: {e}")
            return False
    
    def ask_ai(self, prompt: str, keep_history: bool = True, auto_search: bool = True) -> Optional[str]:
        """Ask AI a question with optional web search fallback and personal data extraction"""
        try:
          
            personal_info = self.extract_personal_info(prompt)
            if personal_info:
                self.update_user_data(personal_info)
            

            if self.needs_time_info(prompt):
                time_info = self.get_istanbul_time_detailed()
                print(f"Current time: {time_info}")
                reply = f"It's currently {time_info}."
                
                if keep_history:
                    self.conversation_history.append({"role": "user", "content": prompt})
                    self.conversation_history.append({"role": "assistant", "content": reply})
                
                return reply
            
            url = f"{self.lm_studio_url}/v1/chat/completions"
            headers = {"Content-Type": "application/json"}
            

            system_prompt_with_context = self.system_prompt
            user_context = self.get_user_context()
            if user_context:
                system_prompt_with_context += f" {user_context}"
            
            messages = [{"role": "system", "content": system_prompt_with_context}]
            
            if keep_history:
                messages.extend(self.conversation_history[-8:]) 
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 150
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                

                reply = self.filter_asterisk_actions(reply)
                
                print(f" Testudo: {reply}")
                
        
                if auto_search and self.should_search_web(reply, prompt):
                    print(" Searching Google for more information...")
                    search_result = self.search_google(prompt)
                    
                    if search_result:
                     question_lower = prompt.lower().strip()
                        w_words = ["who", "what", "when", "where", "why", "which"]
                        is_w_question = any(question_lower.startswith(w_word) for w_word in w_words)
                        
                        if is_w_question:
                            enhanced_reply = search_result
                        else:
                            enhanced_reply = f"I don't know that off the top of my head, but I found: {search_result}"
                        
                     
                        enhanced_reply = self.filter_asterisk_actions(enhanced_reply)
                        
                        print(f"Testudo (web-enhanced): {enhanced_reply}")
                        
                        if keep_history:
                            self.conversation_history.append({"role": "user", "content": prompt})
                            self.conversation_history.append({"role": "assistant", "content": enhanced_reply})
                        
                        return enhanced_reply
                    else:
                        
                        if keep_history:
                            self.conversation_history.append({"role": "user", "content": prompt})
                            self.conversation_history.append({"role": "assistant", "content": reply})
                        return reply
                else:
                   
                    if keep_history:
                        self.conversation_history.append({"role": "user", "content": prompt})
                        self.conversation_history.append({"role": "assistant", "content": reply})
                    return reply
                
            else:
                print(f"AI request failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"AI error: {e}")
            return None
    
    async def speak(self, text: str, filename: str = "response.wav") -> bool:
        """Convert text to speech"""
        try:
            if not text:
                return False
            
            communicate = edge_tts.Communicate(text, voice=self.voice)
            await communicate.save(filename)
            print(f"Audio saved: {filename}")
            return True
        except Exception as e:
            print(f"TTS error: {e}")
            return False
    
    async def chat(self, message: str, with_voice: bool = True, auto_search: bool = True) -> Optional[str]:
        """Complete chat interaction with optional web search"""
        print(f"You: {message}")
        

        reply = self.ask_ai(message, auto_search=auto_search)
        if not reply:
            return None
        
  
        if with_voice:
            await self.speak(reply)
        
        return reply
    
    def clear_history(self):
        """Clear conversation memory"""
        self.conversation_history = []
        print("🧹 History cleared")
    
    def search_google(self, query: str) -> Optional[str]:
        """Search Google and return first relevant sentence"""
        try:

            search_query = quote_plus(query)
            url = f"https://www.google.com/search?q={search_query}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:

                text = response.text
                
               
                snippet_patterns = [
                    r'class="BNeawe[^"]*"[^>]*>([^<]+)</span>',
                    r'class="hgKElc"[^>]*>([^<]+)</span>',
                    r'class="st"[^>]*>([^<]+)</span>',
                ]
                
                for pattern in snippet_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                     
                        for match in matches:
                            sentence = match.strip()

                            if len(sentence) > 20 and not any(skip in sentence.lower() for skip in ['search', 'more', 'about', 'sign in', 'images']):
                         
                                sentence = sentence.replace('&quot;', '"').replace('&amp;', '&').replace('&#39;', "'")
                                print(f"🔍 Google says: {sentence}")
                                return sentence
                
               
                div_pattern = r'<div[^>]*>([^<]+)</div>'
                div_matches = re.findall(div_pattern, text)
                for match in div_matches:
                    sentence = match.strip()
                    if len(sentence) > 30 and len(sentence) < 200:
                        if not any(skip in sentence.lower() for skip in ['search', 'more', 'about', 'sign in', 'images', 'videos']):
                            sentence = sentence.replace('&quot;', '"').replace('&amp;', '&').replace('&#39;', "'")
                            print(f"🔍 Google found: {sentence}")
                            return sentence
                
                print("🔍 No clear answer found in search results")
                return None
                
            else:
                print(f"❌ Google search failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Search error: {e}")
            return None
    
    def should_search_web(self, ai_response: str, original_question: str = "") -> bool:
        """Check if AI response indicates it doesn't know something OR if it's a W question"""
        if not ai_response:
            return False
        
        if original_question:
            question_lower = original_question.lower().strip()
            w_words = ["who", "what", "when", "where", "why", "which"]
            if any(question_lower.startswith(w_word) for w_word in w_words):
                print(f"🔍 Detected W question: '{original_question}' - auto searching web")
                return True
        
     
        unknown_phrases = [
            "not in my codebase",
            "don't know",
            "i don't know",
            "not sure",
            "i'm not sure",
            "can't help",
            "don't have information",
            "not familiar",
            "i don't have",
            "beyond my knowledge",
            "i cannot",
            "i can't",
            "no information",
            "not aware",
            "i'm not aware"
        ]
        
        response_lower = ai_response.lower()
        return any(phrase in response_lower for phrase in unknown_phrases)


def quick_chat(message: str, model: str = "emotion-llama") -> str:
    """Quick chat without history"""

    time_keywords = ["what time", "what's the time", "current time", "time is it",
                    "what date", "what's the date", "current date", "date today",
                    "today", "now", "current", "when is it"]
    
    if any(keyword in message.lower() for keyword in time_keywords):
        istanbul_tz = timezone(timedelta(hours=3))
        now = datetime.now(istanbul_tz)
        time_info = now.strftime("%A, %B %d, %Y at %H:%M (Istanbul time)")
        reply = f"It's currently {time_info}."
        print(f"Testudo: {reply}")
        return reply
    
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Testudo, an ai enabled pet like companion. Designed as an turtle. Reply in 1–2 short natural sentences. Avoid emoticons or roleplay stage directions. Don't call people 'friend', 'creator', or other names unless you know their actual name from the conversation. Never use asterisks for actions or movements."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        reply = response.json()["choices"][0]["message"]["content"]
        

        reply = re.sub(r'\*[^*]*\*', '', reply)
        reply = re.sub(r'\s+', ' ', reply).strip()
        
        print(f"Testudo: {reply}")
        return reply
    except Exception as e:
        print(f"Error: {e}")
        return ""

async def chat_with_voice(message: str, model: str = "emotion-llama") -> str:
    """Chat and generate voice response"""
    reply = quick_chat(message, model)
    if reply:
        communicate = edge_tts.Communicate(reply, voice="en-US-JennyNeural")
        await communicate.save("response.wav")
        print(" Audio saved: response.wav")
    return reply


async def talk_to_testudo(user_message: str, 
                         enable_voice: bool = True,
                         remember_context: bool = True,
                         auto_search: bool = True) -> Optional[str]:
    """Main function to chat with Testudo with optional web search"""
    

    testudo = TestudoAI()
    

    if not testudo.check_connection():
        print("Start LM Studio first!")
        return None
    

    start_time = time.time()
    response = await testudo.chat(user_message, with_voice=enable_voice, auto_search=auto_search)
    elapsed = time.time() - start_time
    
    print(f"Took {elapsed:.2f} seconds")
    return response

async def test_personal_data():
    """Quick test of personal data functionality"""
    print("Testing Personal Data Features\n")
    
    testudo = TestudoAI(user_data_file="test_user_data.json")
    

    test_messages = [
        "My name is Alice and I'm 28 years old",
        "I live in New York and work as a designer",
        "Call me Bob, I'm from London",
        "I am 35 years old and work as a teacher",
        "I'm a 22 year old student"
    ]
    
    for msg in test_messages:
        print(f"Testing: '{msg}'")
        extracted = testudo.extract_personal_info(msg)
        if extracted:
            print(f"Extracted: {extracted}")
            testudo.update_user_data(extracted)
        else:
            print("No personal data detected")
        print()
    
    print("Final user data:")
    testudo.show_user_data()
    

    if os.path.exists("test_user_data.json"):
        os.remove("test_user_data.json")


async def main():
    """Example usage with personal data saving, web search, and time info"""
    
    print("Testudo AI with Personal Data Memory\n")
    

    print("=== Example 1: Normal Chat ===")
    await talk_to_testudo("My name is Ed!")
    

    print("\n=== Example 2: Personal Data Saving ===")
    testudo = TestudoAI()

    print("\n=== Example 3: Using Personal Data ===")
    if testudo.check_connection():
        await testudo.chat("What's my name?", with_voice=False)
        await testudo.chat("How old am I?", with_voice=False)
        await testudo.chat("Where do I live?", with_voice=False)
        await testudo.chat("What's my job?", with_voice=False)
    
    

if __name__ == "__main__":

    asyncio.run(main())
