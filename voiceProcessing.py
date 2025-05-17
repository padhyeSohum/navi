import speech_recognition as sr
import pyautogui
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import google.generativeai as genai

#gemini Config
GEMINI_API_KEY = "AIzaSyCZiuc4uUORjeEKsrjeoNppwBIXGfvZFWg"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

#initialize browser driver (using Chrome)
driver = None

def listen_to_speech():
    """Capture speech from microphone and return as text"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return None
    except sr.RequestError as e:
        print(f"Speech recognition error: {e}")
        return None

def process_command_with_gemini(command):
    """Send command to Gemini API for interpretation"""
    #prompt to guide the AI's response
    system_prompt = """
    You are a web automation assistant. Your job is to interpret natural language commands 
    into specific web actions. Respond ONLY with a JSON object containing:
    - "action": the type of action (e.g., "key_press", "click", "type", "navigate")
    - "details": specific parameters for the action (e.g., which key to press, text to type, URL to navigate to)
    
    Example commands and responses:
    
    User: "pause the video"
    Response: {"action": "key_press", "details": {"key": "k"}}
    
    User: "search for yellow bananas"
    Response: {"action": "type", "details": {"text": "yellow bananas", "follow_with": "ENTER"}}
    
    User: "go to YouTube"
    Response: {"action": "navigate", "details": {"url": "https://youtube.com"}}
    """
    
    try:
        response = model.generate_content(
            system_prompt + "\n\nUser: " + command + "\nResponse:"
        )
        #extract the JSON part from gemini output
        response_text = response.text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]  #remove markdown json markers
        return json.loads(response_text)
    except Exception as e:
        print(f"Error processing command with Gemini: {e}")
        return None

def execute_action(action_data):
    """Execute the web action based on Gemini's response"""
    if not action_data:
        return False
    
    action = action_data.get("action")
    details = action_data.get("details", {})
    
    try:
        if action == "key_press":
            key = details.get("key")
            if key:
                pyautogui.press(key)
                print(f"Pressed key: {key}")
                
        elif action == "type":
            text = details.get("text", "")
            pyautogui.write(text)
            
            follow_with = details.get("follow_with")
            if follow_with:
                pyautogui.press(follow_with.lower())
            print(f"Typed: {text}")
            
        elif action == "navigate":
            url = details.get("url")
            if url:
                driver.get(url)
                print(f"Navigated to: {url}")
                
        elif action == "click":
            pyautogui.click()
            print("Clicked at current position")
            
        else:
            print(f"Unknown action: {action}")
            return False
            
        return True
    except Exception as e:
        print(f"Error executing action: {e}")
        return False

def main():
    global driver
    driver = webdriver.Chrome()

    print("Web Automation Assistant - Speak your command")
    while True:
        try:
            #listen for speech
            command = listen_to_speech()
            if not command:
                continue
                
            #process with Gemini
            print("Processing command...")
            action_data = process_command_with_gemini(command)
            if not action_data:
                print("Could not interpret command")
                continue
                
            #perform action
            if execute_action(action_data):
                print("Action executed successfully")
            else:
                print("Failed to execute action")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            driver.quit()
            break

# if __name__ == "__main__":
#     main()