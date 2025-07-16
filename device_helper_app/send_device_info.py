import tkinter as tk
from tkinter import messagebox
import subprocess
import requests
import json

def get_serial_number(command, keyword):
    try:
        output = subprocess.check_output(command, shell=True).decode().strip()
        return output if output else None
    except Exception:
        return None

def fetch_and_send():
    username = username_entry.get().strip()
    if not username:
        messagebox.showerror("Error", "Please enter your username")
        return

    bios_serial = get_serial_number("powershell -Command \"(Get-WmiObject win32_bios).SerialNumber\"", "")
    baseboard_serial = get_serial_number("powershell -Command \"(Get-WmiObject win32_baseboard).SerialNumber\"", "")

    if not bios_serial or not baseboard_serial:
        messagebox.showerror("Error", "Could not fetch BIOS or Baseboard serial numbers.")
        return

    data = {
        "bios": bios_serial,
        "baseboard": baseboard_serial,
        "username": username
    }

    try:
        url = "http://127.0.0.1:8000/device_verification_bridge/"

        # 👇✅ FIXED LINE — use json=data instead of manually dumping it
        response = requests.post(url, json=data)

        if response.status_code == 200:
            result = response.json()
            messagebox.showinfo("Success", result.get("status", "Information sent."))
        else:
            messagebox.showerror("Server Error", f"Server responded with error:\n{response.text}")
    except Exception as e:
        messagebox.showerror(
            "Connection Failed",
            f"Could not reach the verification server.\n\nPlease make sure:\n"
            "- Your Django server is running\n"
            "- Your firewall or antivirus is not blocking the request\n"
            "- You're connected to the correct network\n\n\nDetails:\n{e}"
        )

# GUI Window
app = tk.Tk()
app.title("Device Verification Helper")
app.geometry("340x210")
app.resizable(False, False)
app.attributes('-topmost', True)  # Always float on top

tk.Label(app, text="Enter your staff username:").pack(pady=10)
username_entry = tk.Entry(app, width=30)
username_entry.pack()

send_button = tk.Button(app, text="Send Device Info", command=fetch_and_send)
send_button.pack(pady=20)

app.mainloop()
