import speech_recognition as sr
import re

def capture_voice_input():
    recognizer = sr.Recognizer()
    
    # Adjust for ambient noise to improve recognition
    with sr.Microphone() as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        print("Listening... Speak your expense:")
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")

            # Try to extract amount using regex - look for numbers with optional rupee symbols
            amount_match = re.search(r'(?:rs\.?|₹|rupees?)?\s*(\d+(?:\.\d{1,2})?)(?:\s*(?:rs\.?|₹|rupees?))?', text.lower())
            amount = float(amount_match.group(1)) if amount_match else 0.0

            # Remove the amount and currency references from text to get description
            description = re.sub(r'(?:rs\.?|₹|rupees?)?\s*(\d+(?:\.\d{1,2})?)(?:\s*(?:rs\.?|₹|rupees?))?', '', text, flags=re.IGNORECASE).strip().capitalize()

            return description, amount

        except sr.UnknownValueError:
            return "Could not understand", 0.0
        except sr.RequestError:
            return "API error", 0.0
        except Exception as e:
            print(f"Error in voice recognition: {str(e)}")
            return f"Error: {str(e)}", 0.0
