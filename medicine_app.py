import csv
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

import paho.mqtt.client as mqtt

BROKER = "localhost"
COMMAND_TOPIC = "medicine/command"
EVENT_TOPIC = "medicine/event"
LOG_FILE = "medicine_log.csv"


class CaretakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Medication Reminder")

        self.alarm_time = ""
        self.alarm_enabled = False
        self.alarm_done_today = ""

        self.create_log_file()
        self.build_gui()
        self.setup_mqtt()
        self.load_logs()
        self.check_alarm_time()

    def create_log_file(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Pi Time", "Event", "Arduino Time"])

    def build_gui(self):
        title = tk.Label(self.root, text="Smart Medication Reminder", font=("Arial", 18, "bold"))
        title.pack(pady=10)

        self.status_label = tk.Label(self.root, text="Status: Starting...", font=("Arial", 12))
        self.status_label.pack(pady=5)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        start_button = tk.Button(button_frame, text="Start Reminder", width=18, command=self.start_reminder)
        start_button.grid(row=0, column=0, padx=5)

        stop_button = tk.Button(button_frame, text="Stop Alarm", width=18, command=self.stop_alarm)
        stop_button.grid(row=0, column=1, padx=5)

        alarm_frame = tk.Frame(self.root)
        alarm_frame.pack(pady=10)

        tk.Label(alarm_frame, text="Alarm time HH:MM").grid(row=0, column=0, padx=5)
        self.alarm_entry = tk.Entry(alarm_frame, width=10)
        self.alarm_entry.grid(row=0, column=1, padx=5)

        set_alarm_button = tk.Button(alarm_frame, text="Set Alarm", command=self.set_alarm)
        set_alarm_button.grid(row=0, column=2, padx=5)

        self.alarm_label = tk.Label(self.root, text="No scheduled alarm set")
        self.alarm_label.pack(pady=5)

        self.log_table = ttk.Treeview(self.root, columns=("pi_time", "event", "arduino_time"), show="headings")
        self.log_table.heading("pi_time", text="Pi Time")
        self.log_table.heading("event", text="Event")
        self.log_table.heading("arduino_time", text="Arduino Time")
        self.log_table.pack(pady=10, padx=10, fill="both", expand=True)

    def setup_mqtt(self):
        try:
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.connect(BROKER, 1883, 60)
            self.client.loop_start()
        except Exception as error:
            messagebox.showerror("MQTT error", f"Could not connect to MQTT broker: {error}")
            self.status_label.config(text="Status: MQTT connection failed")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.status_label.config(text="Status: Connected to MQTT broker")
            client.subscribe(EVENT_TOPIC)
        else:
            self.status_label.config(text=f"Status: MQTT connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        parts = message.split(",", 1)
        event = parts[0]
        arduino_time = parts[1] if len(parts) > 1 else ""

        self.save_log(event, arduino_time)
        self.update_status(event)
        self.load_logs()

    def update_status(self, event):
        if event == "TAKEN":
            self.status_label.config(text="Status: Medicine taken")
        elif event == "MISSED":
            self.status_label.config(text="Status: Medicine missed")
        elif event == "REMINDER_STARTED":
            self.status_label.config(text="Status: Reminder active")
        elif event == "STOPPED":
            self.status_label.config(text="Status: Alarm stopped")
        else:
            self.status_label.config(text=f"Status: {event}")

    def start_reminder(self):
        self.client.publish(COMMAND_TOPIC, "START")
        self.save_log("START_SENT_BY_CARETAKER", "")
        self.load_logs()
        self.status_label.config(text="Status: START command sent")

    def stop_alarm(self):
        self.client.publish(COMMAND_TOPIC, "STOP")
        self.save_log("STOP_SENT_BY_CARETAKER", "")
        self.load_logs()
        self.status_label.config(text="Status: STOP command sent")

    def set_alarm(self):
        entered_time = self.alarm_entry.get().strip()
        try:
            datetime.strptime(entered_time, "%H:%M")
        except ValueError:
            messagebox.showerror("Invalid time", "Please enter the alarm time in HH:MM format.")
            return

        self.alarm_time = entered_time
        self.alarm_enabled = True
        self.alarm_done_today = ""
        self.alarm_label.config(text=f"Scheduled alarm set for {self.alarm_time}")
        self.save_log("ALARM_SET_BY_CARETAKER", self.alarm_time)
        self.load_logs()

    def check_alarm_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = now.strftime("%Y-%m-%d")

        if self.alarm_enabled and current_time == self.alarm_time:
            if self.alarm_done_today != today:
                self.client.publish(COMMAND_TOPIC, "START")
                self.save_log("SCHEDULED_ALARM_TRIGGERED", "")
                self.alarm_done_today = today
                self.load_logs()
                self.status_label.config(text="Status: Scheduled alarm triggered")

        self.root.after(1000, self.check_alarm_time)

    def save_log(self, event, arduino_time):
        pi_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([pi_time, event, arduino_time])

    def load_logs(self):
        for item in self.log_table.get_children():
            self.log_table.delete(item)

        if not os.path.exists(LOG_FILE):
            return

        with open(LOG_FILE, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) == 3:
                    self.log_table.insert("", "end", values=row)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("750x500")
    app = CaretakerApp(root)
    root.mainloop()
