import pyttsx3


def speak(text):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        return False