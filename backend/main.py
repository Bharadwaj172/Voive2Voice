import json  # To convert dictionary to JSON
from ollama import chat
import speech_recognition as sr
from datetime import date
from gtts import gTTS
from io import BytesIO
from pygame import mixer
import threading
import queue
import time

# Initialize the mixer for playing audio
mixer.init()

today = str(date.today())

numtext = 0
numtts = 0
numaudio = 0

messages = []

# Function to handle chat interaction with the LLaMA model
def chatfun(request, text_queue, llm_finished):
    global numtext, messages

    messages.append({'role': 'user', 'content': request})

    response = chat(
        model='llama3.1',
        messages=messages,
        stream=True,
    )

    shortstring = ''
    reply = ''
    append2log(f"AI: ")

    for chunk in response:
        ctext = chunk['message']['content']
        shortstring = "".join([shortstring, ctext])

        if len(shortstring) > 40:
            print(shortstring, end='', flush=True)
            text_queue.put(shortstring.replace("*", ""))
            numtext += 1
            reply = "".join([reply, shortstring])
            shortstring = ''
        else:
            continue

        time.sleep(0.2)

    if len(shortstring) > 0:
        print(shortstring, end='', flush=True)
        shortstring = shortstring.replace("*", "")
        text_queue.put(shortstring)
        numtext += 1
        reply = "".join([reply, shortstring])

    messages.append({'role': 'assistant', 'content': reply})
    append2log(f"{reply}")
    llm_finished.set()  # Signal completion of the text generation by LLM

# Function to convert text to speech and play it
def speak_text(text):
    mp3file = BytesIO()
    tts = gTTS(text, lang="en", tld='us')
    tts.write_to_fp(mp3file)

    mp3file.seek(0)

    try:
        mixer.music.load(mp3file, "mp3")
        mixer.music.play()
        while mixer.music.get_busy():
            time.sleep(0.1)

    except KeyboardInterrupt:
        mixer.music.stop()
        mp3file.close()

    mp3file.close()

# Function to log the conversation
def append2log(text):
    global today
    fname = 'chatlog-' + today + '.txt'
    with open(fname, "a", encoding='utf-8') as f:
        f.write(text + "\n")
        f.close()

# Function to validate phone number
def validate_phone_number(phone):
    phone = phone.replace(" ", "").replace("-", "")
    if len(phone) == 10 and phone.isdigit():
        return phone
    return None

# Enhanced function to validate gender
def validate_gender(gender):
    gender = gender.lower()

    # If the input contains or starts with 'm', treat it as 'male'
    if 'm' in gender:
        return "male"
    # If the input contains or starts with 'f', treat it as 'female'
    elif 'f' in gender:
        return "female"
    return None

# Main function to drive the conversation
def main():
    global today, numtext, numtts, numaudio, messages

    # Ensure that `speech_recognition` is working properly
    rec = sr.Recognizer()
    mic = sr.Microphone()

    # Setup recognizer parameters
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400
    sleeping = False  # AI is initially not in sleep mode, ready to ask questions
    question_idx = 0  # Start from the first question

    # Dictionary to store the user's answers
    user_details = {
        "Name": "",
        "Phone Number": "",
        "Gender": "",
        "Profession": "",
        "Address": ""
    }

    # List of predefined questions for AI to ask the user
    questions = [
        "What is your name?",
        "What is your phone number?",
        "What is your gender?",
        "What is your profession?",
        "What is your address?",
    ]

    question_keys = list(user_details.keys())  # Keys corresponding to each question in the dictionary

    # Flag to track whether the category was selected
    category_selected = False

    # Welcome message and category selection
    welcome_message = "Welcome to the complaint portal. Please let me know to which your problem belongs to. 1) Women/children related crime, 2) Financial crime, 3) Other cyber crime."
    speak_text(welcome_message)
    print("AI: Welcome to the complaint portal. Please let me know to which your problem belongs to. 1) Women/children related crime, 2) Financial crime, 3) Other cyber crime.")
    append2log(f"AI: {welcome_message}")

    # Main loop to handle the conversation flow
    while True:
        with mic as source:
            rec.adjust_for_ambient_noise(source, duration=1)
            print("Listening...")

            # If the category has not been selected yet
            if not category_selected:
                print("Listening for category selection...")
                try:
                    audio = rec.listen(source, timeout=20, phrase_time_limit=30)
                    user_response = rec.recognize_google(audio, language="en-EN")
                    category = user_response.lower()

                    append2log(f"You: {category}")
                    print(f"You: {category}")

                    if "1" in category or "women" in category or "children" in category:
                        category_selection = "Women/children related crime"
                    elif "2" in category or "financial" in category:
                        category_selection = "Financial crime"
                    elif "3" in category or "cyber" in category:
                        category_selection = "Other cyber crime"
                    else:
                        speak_text("I didn't understand that. Please select 1, 2, or 3.")
                        continue  # Ask again if the category was not understood

                    # Log and respond based on category selection
                    speak_text(f"You selected {category_selection}. Let's start with some questions.")
                    print(f"AI: You selected {category_selection}. Let's start with some questions.")
                    append2log(f"AI: You selected {category_selection}. Let's start with some questions.")

                    # Set flag to true and start asking questions
                    category_selected = True
                    sleeping = False  # Now the AI will proceed with questions
                    continue  # After selecting category, start asking the questions

                except Exception as e:
                    print(f"Error: {e}")
                    continue

            # Ask the next question
            if category_selected and not sleeping and question_idx < len(questions):
                question = questions[question_idx]
                print(f"AI: {question}")
                append2log(f"AI: {question}")
                speak_text(question)

                question_idx += 1  # Move to the next question
                sleeping = True  # AI now waits for the user's response

            print("Listening for user response...")
            try:
                # Listen for the user's response
                audio = rec.listen(source, timeout=20, phrase_time_limit=30)
                user_response = rec.recognize_google(audio, language="en-EN")
                request = user_response.lower()

                # Log and print user response
                append2log(f"You: {request}")
                print(f"You: {request}")

                # After user responds, AI asks the next question
                sleeping = False  # AI will ask the next question in the next loop

                # Validate responses based on the question
                if question_idx == 2:  # Phone number validation
                    validated_phone = validate_phone_number(user_response)
                    if not validated_phone:
                        speak_text("Please provide a valid 10-digit phone number.")
                        question_idx -= 1  # Repeat the phone number question
                        continue
                    user_details[question_keys[question_idx - 1]] = validated_phone

                elif question_idx == 3:  # Gender validation
                    validated_gender = validate_gender(user_response)
                    if not validated_gender:
                        speak_text("Please specify your gender as either 'male' or 'female'.")
                        question_idx -= 1  # Repeat the gender question
                        continue
                    user_details[question_keys[question_idx - 1]] = validated_gender

                else:
                    # Save the user's response in the dictionary
                    user_details[question_keys[question_idx - 1]] = user_response

                # Once all questions have been asked, the AI will say goodbye
                if question_idx >= len(questions):
                    speak_text("Thank you for answering all my questions. Here are the details you provided.")
                    append2log("AI: Thank you for answering all my questions. Here are the details you provided.")
                    
                    # Convert the user details to JSON and display it
                    user_details_json = json.dumps(user_details, indent=4)
                    print(user_details_json)  # Print JSON to the console
                    append2log(user_details_json)  # Log the JSON output
                    speak_text("Goodbye!")
                    break

            except Exception as e:
                print(f"Error: {e}")
                continue

if __name__ == "__main__":
    main()
