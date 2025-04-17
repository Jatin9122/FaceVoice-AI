import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import itertools
import cv2
import speech_recognition as sr
import datetime, threading, os, subprocess 
import pyttsx3, pygame

# Setup
recognizer = sr.Recognizer()
speaker = pyttsx3.init()
music_folder = "Add your music folder path"

# Helpers 
def speak(text):
    speaker.say(text)
    speaker.runAndWait()

# Voice Command
def get_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good Morning"
    elif hour < 18:
        return "Good Afternoon"
    return "Good Evening"

def recognize_voice():
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=5)
            return recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return "Sorry, I did not understand that."
        except sr.RequestError:
            return "Sorry, the speech service is down."
        except sr.WaitTimeoutError:
            return "No speech detected."

# Different Action
def open_notepad():
    try:
        subprocess.Popen(["notepad.exe"])
        return "Notepad opened successfully!"
    except Exception as e:
        return f"Could not open Notepad. Error: {e}"

def close_notepad():
    try:
        os.system("taskkill /f /im notepad.exe")
        return "Notepad closed successfully!"
    except Exception as e:
        return f"Could not close Notepad. Error: {e}"

def play_music():
    try:
        files = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav'))]
        if not files:
            return "No music files found."
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join(music_folder, files[0]))
        pygame.mixer.music.play()
        return f"Playing {files[0]}"
    except Exception as e:
        return f"Error playing music: {e}"

# Face Detection 
def face_scan():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)
    detected = False
    start_time = cv2.getTickCount()

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            detected = True
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.putText(frame, "Face Scan: Press 'q' to exit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Face Scanner', frame)

        elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
        if detected or cv2.waitKey(1) & 0xFF == ord('q') or elapsed > 5:
            break

    cap.release()
    cv2.destroyAllWindows()
    return detected

# GUI Application
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Assistant")
        self.root.state('zoomed')

        self.frame_image = tk.Frame(self.root)
        self.frame_gif = tk.Frame(self.root)

        self.gif_running = False
        self.listening = False

        self.image_path = "Chatbot.webp"
        self.gif_path = "speak.gif"

        self.load_fullscreen_image()
        self.load_gif_frame()
        self.show_image_frame()

    def load_fullscreen_image(self):
        image = Image.open(self.image_path)
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        image = image.resize((w, h), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(image)

        self.label_image = tk.Label(self.frame_image, image=self.bg_image)
        self.label_image.pack(fill="both", expand=True)

        self.start_button = tk.Button(self.frame_image, text="Start", font=('Arial', 20),
                                      bg="blue", fg="white", command=self.start_speech_ui)
        self.stop_button = tk.Button(self.frame_image, text="Exit", font=('Arial', 20),
                                     bg="blue", fg="white", command=self.root.destroy)

        self.label_image.place(x=0, y=0, relwidth=1, relheight=1)
        self.start_button.place(relx=0.40, rely=0.9)
        self.stop_button.place(relx=0.50, rely=0.9)

    def load_gif_frame(self):
        self.gif_label = tk.Label(self.frame_gif, bg="skyblue", anchor="center")
        self.gif_label.pack(fill="both", expand=True)

        self.output_label = tk.Label(self.frame_gif, text="", font=('Arial', 18),
                                      wraplength=800, justify="center")
        self.output_label.pack(pady=20)

        self.stop_button_gif = tk.Button(self.frame_gif, text="Stop", font=('Arial', 20),
                                         bg="skyblue", fg="white", command=self.stop_speech_ui)
        self.stop_button_gif.place(relx=0.9, rely=0.95, anchor="center")

        gif = Image.open(self.gif_path)
        self.frames = [ImageTk.PhotoImage(f.copy().convert("RGBA")) for f in ImageSequence.Iterator(gif)]
        self.frame_iter = itertools.cycle(self.frames)

    def animate_gif(self):
        if self.gif_running:
            self.gif_label.configure(image=next(self.frame_iter))
            self.root.after(100, self.animate_gif)

    def show_image_frame(self):
        self.gif_running = False
        self.frame_gif.pack_forget()
        self.frame_image.pack(fill="both", expand=True)

    def show_gif_frame(self):
        self.frame_image.pack_forget()
        self.frame_gif.pack(fill="both", expand=True)
        self.gif_running = True
        self.animate_gif()

    def start_speech_ui(self):
        self.show_gif_frame()
        self.listening = True
        threading.Thread(target=self.voice_loop).start()

    def stop_speech_ui(self):
        self.listening = False
        self.show_image_frame()

    def voice_loop(self):
        greet = get_greeting()
        self.show_text(greet)
        speak(greet)

        while self.listening:
            command = recognize_voice()
            if not self.listening:
                break

            response = ""
            if "morning" in command:
                response = "Good Morning"
            elif "afternoon" in command:
                response = "Good Afternoon"
            elif "evening" in command:
                response = "Good Evening"
            elif "open notepad" in command:
                response = open_notepad()
            elif "close notepad" in command:
                response = close_notepad()
            elif "play music" in command:
                response = play_music()
            elif "exit" in command or "stop" in command:
                response = "Goodbye!"
                self.stop_speech_ui()
            else:
                response = f"You said: {command}"

            self.show_text(response)
            speak(response)

    def show_text(self, text):
        self.output_label.config(text=text)

# Main Entry
if __name__ == "__main__":
    if face_scan():
        root = tk.Tk()
        App(root)
        root.mainloop()
    else:
        print("Face not detected. Application closed.")
