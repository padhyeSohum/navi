import cv2
import face_recognition
import numpy as np
import os
import uuid
import base64
import re
import threading
import pyautogui
import time
import speech_recognition as sr
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import google.generativeai as genai

KNOWN_FACE_DIR = 'known_faces'
os.makedirs(KNOWN_FACE_DIR, exist_ok=True)

GEMINI_API_KEY = "AIzaSyCZiuc4uUORjeEKsrjeoNppwBIXGfvZFWg"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')

#head movement control variables
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)
running = True

#mouse control parameters
screen_width, screen_height = pyautogui.size()
smoothing_factor = 0.5
prev_x, prev_y = pyautogui.position()

#position history
position_history = []

#control zone parameters
control_zone_active = True
control_zone_size = 0.1

#selenium browser setup (non-anonymous)
chrome_options = Options()

driver = webdriver.Chrome(options=chrome_options)
#driver.get("https://www.google.com")

def listen_to_speech():
    recognizer = sr.Recognizer()
    while running:
        with sr.Microphone() as source:
            print("Listening...")
            try:
                audio = recognizer.listen(source, timeout=5)
            except sr.WaitTimeoutError:
                continue

        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            process_command(text)
        except sr.UnknownValueError:
            print("Could not understand audio")
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")

def process_command(command):
    if not command:
        return

    if command.lower().startswith(("search for", "search ", "look up", "find")):
        perform_search(command)
        return

    print("Processing command...")
    action_data = process_command_with_gemini(command)
    if not action_data:
        print("Could not interpret command")
        return

    if execute_action(action_data):
        print("Action executed successfully")
    else:
        print("Failed to execute action")

def perform_search(command):
    try:
        if command.lower().startswith("search for"):
            query = command[10:].strip()
        elif command.lower().startswith("search "):
            query = command[7:].strip()
        elif command.lower().startswith("look up"):
            query = command[7:].strip()
        elif command.lower().startswith("find"):
            query = command[4:].strip()
        else:
            query = command.strip()

        if not query:
            print("No search query provided")
            return

        print(f"Searching for: {query}")

        pyautogui.hotkey('command', 'l')
        time.sleep(0.5)
        pyautogui.hotkey('command', 'a')
        pyautogui.press('backspace')
        pyautogui.write(query)
        pyautogui.press('enter')

        print(f"Successfully searched for: {query}")
    except Exception as e:
        print(f"Error performing search: {str(e)}")

def process_command_with_gemini(command):
    system_prompt = """
    You are a computer control assistant. Your job is to interpret natural language commands 
    into specific actions. Respond ONLY with a JSON object containing:
    - "action": the type of action (e.g., "click", "type", "navigate", "scroll", "key_press", "search")
    - "details": specific parameters for the action (e.g., text to type, URL to navigate to, key to press)

    For key presses:
    - Special keys should be lowercase (e.g., "enter", "space", "tab")
    - Letter keys should be lowercase (e.g., "q", "a", "z")
    - Number keys should be strings (e.g., "1", "2")

    Example commands and responses:

    User: "click the button"
    Response: {"action": "click", "details": {}}

    User: "type hello world"
    Response: {"action": "type", "details": {"text": "hello world"}}

    User: "go to YouTube"
    Response: {"action": "navigate", "details": {"url": "https://youtube.com"}}

    User: "scroll down"
    Response: {"action": "scroll", "details": {"direction": "down", "amount": 300}}

    User: "press Q"
    Response: {"action": "key_press", "details": {"key": "q"}}

    User: "press enter"
    Response: {"action": "key_press", "details": {"key": "enter"}}

    User: "press space"
    Response: {"action": "key_press", "details": {"key": "space"}}

    User: "search for python tutorials"
    Response: {"action": "search", "details": {"query": "python tutorials"}}
    """

    try:
        response = model.generate_content(
            system_prompt + "\n\nUser: " + command + "\nResponse:"
        )
        response_text = response.text
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        return json.loads(response_text)
    except Exception as e:
        print(f"Error processing command with Gemini: {e}")
        return None

def execute_action(action_data):
    if not action_data:
        return False

    action = action_data.get("action")
    details = action_data.get("details", {})

    try:
        if action == "click":
            pyautogui.click()
        elif action == "double_click":
            pyautogui.doubleClick()
        elif action == "right_click":
            pyautogui.rightClick()
        elif action == "type":
            text = details.get("text", "")
            pyautogui.write(text)
        elif action == "navigate":
            url = details.get("url")
            if url:
                driver.get(url)
        elif action == "scroll":
            direction = details.get("direction", "down").lower()
            amount = details.get("amount", 300)
            pyautogui.scroll(amount if direction == "up" else -amount)
        elif action == "key_press":
            key = details.get("key")
            if key:
                pyautogui.press(key)
        elif action == "search":
            query = details.get("query")
            if query:
                perform_search(f"search for {query}")
            else:
                return False
        else:
            print(f"Unknown action: {action}")
            return False

        return True
    except Exception as e:
        print(f"Error executing action: {e}")
        return False

def head_movement_control():
    global running, prev_x, prev_y

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        height, width = frame.shape[:2]

        zone_width = int(width * control_zone_size)
        zone_height = int(height * control_zone_size)
        zone_x1 = (width - zone_width) // 2
        zone_y1 = (height - zone_height) // 2
        zone_x2 = zone_x1 + zone_width
        zone_y2 = zone_y1 + zone_height

        cv2.rectangle(frame, (zone_x1, zone_y1), (zone_x2, zone_y2), (0, 255, 255), 2)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        if len(faces) > 0:
            largest_face = max(faces, key=lambda item: item[2] * item[3])
            x, y, w, h = largest_face
            face_center_x = x + w // 2
            face_center_y = y + h // 2

            cv2.circle(frame, (face_center_x, face_center_y), 8, (0, 255, 0), -1)

            if (face_center_x < zone_x1 or face_center_x > zone_x2 or 
                face_center_y < zone_y1 or face_center_y > zone_y2):

                if face_center_x < zone_x1:
                    norm_x = (face_center_x - zone_x1) / zone_x1
                elif face_center_x > zone_x2:
                    norm_x = (face_center_x - zone_x2) / (width - zone_x2)
                else:
                    norm_x = 0

                if face_center_y < zone_y1:
                    norm_y = (face_center_y - zone_y1) / zone_y1
                elif face_center_y > zone_y2:
                    norm_y = (face_center_y - zone_y2) / (height - zone_y2)
                else:
                    norm_y = 0

                scale_factor = 1.5
                norm_x = np.sign(norm_x) * (abs(norm_x) ** scale_factor)
                norm_x = -norm_x
                norm_y = np.sign(norm_y) * (abs(norm_y) ** scale_factor)

                position_history.append((norm_x, norm_y))
                if len(position_history) > 5:
                    position_history.pop(0)

                if position_history:
                    smooth_x = sum(p[0] for p in position_history) / len(position_history)
                    smooth_y = sum(p[1] for p in position_history) / len(position_history)
                else:
                    smooth_x, smooth_y = norm_x, norm_y

                target_x = int(prev_x + (smooth_x * screen_width * 0.8))
                target_y = int(prev_y + (smooth_y * screen_height * 0.8))

                target_x = max(0, min(screen_width - 1, target_x))
                target_y = max(0, min(screen_height - 1, target_y))

                new_x = int(prev_x * (1 - smoothing_factor) + target_x * smoothing_factor)
                new_y = int(prev_y * (1 - smoothing_factor) + target_y * smoothing_factor)

                pyautogui.moveTo(new_x, new_y)
                prev_x, prev_y = new_x, new_y

            cv2.line(frame, (face_center_x, face_center_y), (width // 2, height // 2), (0, 255, 255), 2)

        cv2.putText(frame, "Move head outside yellow box to control cursor", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Say commands like 'click', 'search for cats', or 'press Q'", (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow('Head-Controlled Mouse', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False
            break

def main():
    global running

    print("Starting head-controlled mouse with voice commands...")
    print(f"Screen resolution: {screen_width}x{screen_height}")

    voice_thread = threading.Thread(target=listen_to_speech)
    voice_thread.daemon = True
    voice_thread.start()

    try:
        head_movement_control()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        running = False
        cap.release()
        cv2.destroyAllWindows()
        voice_thread.join()
        driver.quit()

if __name__ == '__main__':
    main()

cv2.destroyAllWindows()