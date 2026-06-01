# Smart Medication Reminder System

This project was created for SIT210 Embedded Systems Development. It is a small embedded and IoT prototype that helps a caretaker send medicine reminders to a patient device and record whether the dose was taken or missed.

The final system uses a Raspberry Pi as the caretaker side and an Arduino Nano 33 IoT as the patient alarm device. The two devices communicate over WiFi using MQTT through a Mosquitto broker running on the Raspberry Pi.

## Demonstration video

https://youtu.be/JR4DQjtWaZQ

## Project files

| File | What it does |
| --- | --- |
| medicine_app.py | Runs the Raspberry Pi caretaker dashboard using Python, Tkinter and MQTT. |
| arduino_patient_device.ino | Runs the Arduino Nano 33 IoT patient alarm device. |
| system_block_diagram.png | Shows the main system components and how they connect. |
| system_flow_diagram.png | Shows the normal reminder process from start to logging. |
| upload_commands_mac.txt | Contains the GitHub upload commands for Mac Terminal. |

## How the system works

The caretaker uses the Python dashboard on the Raspberry Pi to start, stop or schedule a reminder. The Python app publishes START and STOP messages to the MQTT topic `medicine/command`. The Arduino listens to that topic and turns on the OLED display, white LED and buzzer when a reminder starts.

If the patient presses the physical button within 20 seconds, the Arduino marks the dose as taken and publishes a TAKEN event. If the button is not pressed within 20 seconds, it marks the dose as missed and publishes a MISSED event. The Raspberry Pi receives those events through the `medicine/event` topic and saves them into a CSV log.

## Hardware used

| Component | Purpose |
| --- | --- |
| Raspberry Pi | Runs the caretaker dashboard, Mosquitto MQTT broker and CSV logging. |
| Arduino Nano 33 IoT | Works as the patient side alarm device. |
| OLED display | Shows reminder messages to the patient. |
| RTC module | Provides time for Arduino event timestamps. |
| Button | Lets the patient confirm that medicine was taken. |
| White LED | Shows that a reminder is active. |
| Green LED | Shows that the medicine was taken. |
| Red LED | Shows that the dose was missed. |
| Buzzer | Gives an audible medication alarm. |

## MQTT topics

| Topic | Direction | Messages |
| --- | --- | --- |
| medicine/command | Raspberry Pi to Arduino | START, STOP |
| medicine/event | Arduino to Raspberry Pi | ARDUINO_READY, MQTT_CONNECTED, REMINDER_STARTED, TAKEN, MISSED, STOPPED |

## Raspberry Pi setup

Install the required packages:

```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients python3-paho-mqtt python3-tk -y
```

Create the local Mosquitto configuration:

```bash
sudo nano /etc/mosquitto/conf.d/local.conf
```

Add this configuration:

```text
listener 1883
allow_anonymous true
```

Restart Mosquitto:

```bash
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```

Run the caretaker dashboard:

```bash
cd ~/Desktop/SmartMedicationReminder
python3 medicine_app.py
```

## Arduino setup

Open `arduino_patient_device.ino` in the Arduino IDE. Install the required libraries, update the WiFi name and password, then update the MQTT server IP address to match the Raspberry Pi IP address. Upload the code to the Arduino Nano 33 IoT and check the Serial Monitor for WiFi and MQTT connection messages.

## Testing completed

The project was tested by checking the Mosquitto broker, MQTT publish and subscribe messages, manual reminder start, stop command, button confirmation, missed dose timeout, scheduled reminder trigger and CSV logging.
