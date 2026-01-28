"""
===========================================================================
Author          :  Harsha K
Created on      :  07-02-2025
Purpose         :  Fuel tank leak detection system
M.Purpose       :  
Modified by     :  
Modified on     :  
Version         :  1.4.10
===========================================================================
"""
from datetime import datetime
import time
import gc
from tkinter import *
from tkinter import messagebox  
from PIL import Image, ImageTk
#from Detection import obj_detection
from ultralytics import YOLO
from config import *
import cv2
import asyncio
import logging
import psutil
import os
import queue
import threading
import tkinter as tk
import subprocess
import traceback
import pypyodbc
import websockets
import websocket
import requests
import json
import config
from  Img_Process import *
import gc
import imutils
from imutils.video import VideoStream
from pymodbus.client.tcp import ModbusTcpClient

titles = "Fuel Tank Leak Detection System - V1.4.10"
#=================================================================================================  
top = Tk()  
#=================================================================================================
frame = None
bgcolor = "#003366"
#camip = "rtsp://admin:Admin123%23%23%23@"+ Camera_IP +":554/Streaming/Channels/201"
camip = "rtsp://admin:tvsmys%23%23%23@10.30.11.151:554/Streaming/Channels/201"
#cap = cv2.VideoCapture(camip)
cap = VideoStream(camip).start()  # Start video stream (0 is the default webcam)
gc_counter = 0  # To periodically trigger garbage collection
Is_Running = True
_running = True
 
# YOLO model initialization
previous_engine_no = None
mbus = ModbusTcpClient(host= mod_bus_ip, auto_open=True, auto_close=False)
model2 = YOLO('best.pt', task='detect')
model1 = YOLO('last.pt', task='segment')
class_names1 = model1.names
class_names2 = model2.names
frame = None  # This should be set to your input frame from a video or camera
predicted_frame = None
result_data = {"result": ""}
rslt_sts = None  # This should be your GUI label or status display

# Get screen dimensions
screen_width = top.winfo_screenwidth()
screen_height = top.winfo_screenheight()
status_text = ""
status_color = "grey"


#===========================================================================================
ws_data_queue = queue.Queue()
engine_no_var = tk.StringVar()
result_var = tk.StringVar()
detection_queue = queue.Queue()
# Global variables to hold engine data and frame images
engine_no = ""
predict_video = None
live_frame = None
predicted_frame=None
sensor1 = ""

#--------------------------------------------------------------------------------------------------------
# Track & Trace integration code
#--------------------------------------------------------------------------------------------------------
previous_result = None

previous_idfr = ""
idfr = ""
sku_part_no = ""

#===========================================================================
def SaveImage(sts,idfr):
    try:
        global store_predicted_frame

        if msg in ("PASS", "FAIL"):
            print("Image will stored with status:", sts)
            Store_Image(project_id= str(project_id), rslt_sts=sts, frame=store_predicted_frame, body='', remarks=idfr, dbu=True, send_mail=False)
            print("Image saved at :",datetime.now().strftime("%d-%m-%Y_%H_%M_%S")," -> Status:",sts)
    except Exception as ee:
        print("Error in SaveImage:",str(ee))

#=========================================================================
def set_sensor_value(vals, msgs):
    try:
        global detection_flag
        
        print("set_sensor_value method called with status:", msgs, "sensor value:",vals)
        
        #if vals == 1 and msgs != "":
        si = threading.Thread(target=SaveImage, args=(msgs,""))
        si.daemon = True
        si.start()

        sensor_det.config(text=f"Sensor : "+ str(vals))
        rslt_sts.config(text="-",bg="lightgray",fg="white") 
        #msg = ""
        
        #detection_flag = True
        #msg = "FAIL"
        #run_detection()
    except Exception as ee:
        print("Exception in set_sensor_value:",ee)

def Conveyer_Integration(start_stop_bit):
    global mbus
    try:
        #================================================================
        # Stop the conveyer here, since unloading person has to select the part
        #================================================================
        print("Conveyer_Integration method called :",bool(start_stop_bit))
        mbus.write_coil(plc_bit_stop,bool(start_stop_bit))
        #================================================================
    except Exception as ee:
        print("Error in Conveyer_Integration method :", str(ee))

def Read_Sensor():
    
    try:
        #print("Read_Sensor method called")
        global mbus,_running,sensor_triger,msg,idfr_cnt,pidfr_cnt
        msg = ""
        first_time = 0

        false_det = False # To ensure sensor should be False & then it has to be True
            
        while _running:

            regs_list_2 = mbus.read_coils(1,1)
            #regs_list_2 = mbus.read_holding_registers(address=plc_bit_stop,count=2)
            sensor1 = regs_list_2.bits[0]
            #sensor1 = regs_list_2.registers[0]
            sensors = int(sensor1)

            if (sensors == 1 and first_time != sensors): # or (sensor1 == True and first_time == False and false_det == False):
                first_time = sensors
                set_sensor_value(1,msg)
                sensor_det.config(text=f"Sensor : 1")
                msg = ""
                #print("Sensor:",datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
                #threading.Timer(sensor_interval, set_sensor_value, args=(1,)).start()
                #print("Input received from TNT:",idfr)
            elif sensors == 0:
                first_time = sensors
                sensor_det.config(text=f"Sensor : 0")
                #rslt_sts.config(text="-",bg="lightgray",fg="white") 
            
    except Exception as ee:
        print("Error in Read_Sensor:",ee)
 
#===========================================================================================
# Close window function
def close_window():
    global _running
    try:
        _running = False  # Stop the WebSocket connection loop
        top.destroy()  # Close the Tkinter window
        #cap.release()  # Release the webcam
    except Exception as ee:
        pass
#===========================================================================================
def update_clock():
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        clock_label.config(text=current_time)
        clock_label.after(1000, update_clock)
    except Exception as ee:
        pass
#===========================================================================================
def process_frame_imutils(frame, width=800, height=670):
    """Resizes, converts, and prepares a frame for Tkinter display."""
    # Resize while maintaining aspect ratio
    frame_resized = imutils.resize(frame, width=width)
    # Convert to RGB (Tkinter requires RGB format)
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    # Convert to PIL format for Tkinter
    return ImageTk.PhotoImage(Image.fromarray(frame_rgb))
#===========================================================================================
def process_frame(frames, width=800, height=670):
    """Resize and convert frame for Tkinter display."""
    frame_resized = cv2.resize(frames, (width, height), interpolation=cv2.INTER_AREA)
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(frame_rgb))


#===========================================================================================
def update_live_image():
    
    global frame,cap, gc_counter
 
    try:
 
        #ret, frame = cap.read()
        frame = cap.read()

        if True:
            
            logo_photo = process_frame_imutils(frame)

            # Update the Tkinter label
            live_video.config(image=logo_photo)
            live_video.image = logo_photo  # Prevent garbage collection
 
    except Exception as ee:
        pass
 
    # Call this function again after 10ms
    live_video.after(50, update_live_image)
#===========================================================================
def update_predict_image():

    gc_counter = 0
    global frame,predicted_frame

    if frame is not None:

        if predicted_frame is None:
            predicted_frame = frame

        # Example usage inside a video processing loop
        logo_photo = process_frame_imutils(predicted_frame)

        # Update the Tkinter label
        predict_video.config(image=logo_photo)
        predict_video.image = logo_photo  # Prevent garbage collection

    # Call this function again after 10ms
    predict_video.after(50, update_predict_image)
#===========================================================================================
# Function to update engine number and result
def update_engine_data(engine_no, result):
    engine_no_var.set(engine_no)  # Update engine number
    result_var.set(result)  # Update result
#==========================================================================================

def run_detection():
    global frame, predicted_frame, result_data, rslt_sts, store_predicted_frame, msg

    roi_top_left = (222, 0)
    roi_bottom_right = (1273, 713)
    leak_box_color = (0, 0, 255)
    leak_box_thickness = 8

    if not os.path.exists("leak_tanks"):
        os.makedirs("leak_tanks")

    frame_count = 0

    while _running:  # Use a flag to allow graceful exit
        if frame is None:
            time.sleep(0.05)
            continue

        frame_count += 1

        # Process every 3rd frame only to reduce CPU load
        if frame_count % 3 != 0:
            time.sleep(0.01)
            continue

        try:
            display_frame = frame.copy()
            leak_detected = False
            tank_detected = False

            # Run first model - segmentation
            results1 = model1.track(display_frame, conf=0.8, verbose=False, persist=True, imgsz=640)

            # Run second model - detection
            results2 = model2.track(display_frame, conf=0.8, verbose=False, persist=True, imgsz=640)

            # Process combined results
            for results in [results1, results2]:
                for r in results:
                    predicted_frame = r.plot()
                    for box in r.boxes:
                        class_id = int(box.cls)
                        class_name = (model1.names if results == results1 else model2.names)[class_id]
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                        # Check if box inside region of interest
                        if not (roi_top_left[0] <= x1 <= roi_bottom_right[0] and roi_top_left[1] <= y1 <= roi_bottom_right[1]):
                            continue

                        if class_name.upper() == "LEAK":
                            leak_detected = True
                            cv2.rectangle(predicted_frame, (x1, y1), (x2, y2), leak_box_color, leak_box_thickness)
                            cv2.putText(predicted_frame, f"LEAK {box.conf.item():.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, leak_box_color, 2)

                        elif class_name.upper() == "TANK":
                            tank_detected = True

            if leak_detected:
                msg = "FAIL"
                store_predicted_frame = predicted_frame
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                leak_image_filename = f"leak_tanks/Segment_leak_{timestamp}.jpg"
                cv2.imwrite(leak_image_filename, predicted_frame)
                rslt_sts.config(text=msg, bg="red", fg="white")
                result_data["result"] = msg
                print("Leak detected")

                stop_conveyer()  # Stop conveyor when leak detected
                start_conv()     # Start conveyor (not sure if immediate restart is needed here)

            elif tank_detected:
                msg = "PASS"
                store_predicted_frame = predicted_frame
                rslt_sts.config(text=msg, bg="green", fg="white")
                result_data["result"] = msg

            # Run garbage collector every 50 frames to free memory
            if frame_count % 50 == 0:
                gc.collect()

            time.sleep(0.05)  # Small delay to ease CPU load

        except Exception as e:
            print(f"Issue in detection: {e}")
            traceback.print_exc()
            time.sleep(0.1)


#===========================================================================
# Function to start the conveyor based on Modbus TCP
def start_conv():
    try:
       
        c = ModbusTcpClient(host=mod_bus_ip, auto_open=True, auto_close=True)
        if not c.connect():
            print("Failed to connect to Modbus server.")
            return

        while True:
            try:
                
                result = c.read_coils(3, 1) 

                if result.isError():
                    time.sleep(1)  
                    continue  

                sensor1 = int(result.bits[0])  
                if sensor1 == 1:
                    
                    write_result = c.write_coils(17, [0])  

                    if write_result.isError():
                        print(f"Error starting conveyor: {write_result}")
                    else:
                        print("Conveyor started successfully.")
                    
                    
                    detection_thread = threading.Thread(target=run_detection)
                    detection_thread.daemon = True  
                    detection_thread.start()
                    break  

            except Exception as eee:
                print("Modbus read/write error:", eee)
                time.sleep(1)  

    except ValueError as ee:
        print("Value error:", ee)

    finally:
        
        if c:
            c.close()
            print("Connection closed.")


def stop_conveyer():
    try:
        c = ModbusTcpClient(host=mod_bus_ip, auto_open=True, auto_close=True)
        if not c.connect():
            print("Failed to connect to Modbus server")
            return

       
        result = c.write_coil(17, True)  

        if result.isError():
            print(f"Error stopping conveyor: {result}")
        else:
            print("Conveyor stopped successfully.")

        
        read_result = c.read_coils(17, 1)
        if read_result.isError():
            print(f"Error reading coil 17: {read_result}")
        else:
            print(f"Coil 17 status after stop: {read_result.bits[0]}")

    except Exception as ee:
        print(f"Modbus connectivity error: {ee}")
    finally:
        if c:
            c.close()  
#===========================================================================================
# Fullscreen mode (also makes it maximized)
top.wm_attributes("-fullscreen", True)
 
# Top 10% - Title Bar
top_frame = Frame(top, bg="#003366", height=int(screen_height * 0.1))
top_frame.pack(fill="x")
 
# Load the logo image
logo_image = Image.open(dir_path + "/logo.gif")  # Replace with your logo path
logo_photo = ImageTk.PhotoImage(logo_image)
 
# Create a label to display the logo
logo_label = Label(top_frame, image=logo_photo)
logo_label.pack(side=LEFT, padx=10)
 
title_label = Label(top_frame, text= titles , bg=bgcolor, fg="white", font=("Arial", 24),anchor="center") #  anchor="center"
title_label.pack(side = LEFT,expand=True, fill="x", padx=10) # ,expand=True, fill="x"
 
# Custom close button
close_button = Button(top_frame, text="X", bg="red", fg="white", font=("Arial", 12,"bold"), command=close_window)
close_button.pack(side=RIGHT, padx=10)
 
# Clock Label
clock_label = Label(top_frame, bg=bgcolor, fg="white", font=("Arial", 18))
clock_label.pack(side=RIGHT, padx=10)
 
#===============================================================================================
# Main content area
main_frame = Frame(top, bg="white")
main_frame.pack(expand=True, fill="both")
 
# 2 columns split
main_frame1 = Frame(main_frame, bg="whitesmoke")
main_frame1.pack(side=LEFT, expand=True, fill="both")
main_frame1_title = Label(main_frame1, text="Live Video", bg="lightblue", font=("Arial", 24),anchor="center")
main_frame1_title.pack(side = TOP, fill="x", padx=10, pady=5) # expand=True
 
main_frame2 = Frame(main_frame, bg="white")
main_frame2.pack(side=RIGHT,expand=True, fill="both")
main_frame2_title = Label(main_frame2, text="Detected Image", bg="lightblue", font=("Arial", 24),anchor="center")
main_frame2_title.pack(side = TOP,fill="x", padx=10, pady=5)
 
# Create a label to display the OpenCV image
live_video = Label(main_frame1)
live_video.pack(pady=1)
 
predict_video = Label(main_frame2)
predict_video.pack(pady=1)
 
# Result frame
rslt_frame = Frame(top, bg="green", height=40, width=5)  # Reduced height for the frame
rslt_frame.pack(side=TOP, fill="x")
 
# Status label centered
rslt_sts = Label(rslt_frame, text=status_text, bg=status_color, fg="white", font=("Arial", 25), padx=15, pady=5, height=1, width=100)
rslt_sts.pack(side=TOP, expand=True)  # Centering the label
 
# Create a frame for parameter labels (moved below result frame)
engine_frame = Frame(top, bg="whitesmoke")
engine_frame.pack(side=TOP, fill="x", padx=10, pady=5) 

sensor_det = Label(engine_frame, text="Sensor : -", bg="maroon", fg="white", font=("Arial", 25))
sensor_det.pack(side=RIGHT, anchor="w", padx=10, pady=5)
 
params_frame = Frame(top, bg="whitesmoke")
params_frame.pack(side=TOP, fill="x", padx=10, pady=5) 
 
#==============================================================================================
# Top 10% - Bottom Bar
bottom_frame = Frame(top, bg=bgcolor, height=int(screen_height * 0.1))
bottom_frame.pack(fill="x",side=BOTTOM)
bottom_title_label = Label(bottom_frame, text="This application is developed & maintained by D & AI", bg=bgcolor, fg="white", font=("Arial", 24))
bottom_title_label.pack(side = BOTTOM)
 
# Start updating the clock
update_clock()

#Read modbus data
mb = threading.Thread(target=Read_Sensor)
mb.daemon = True
mb.start()
 
#Update live image feed
st = threading.Thread(target=update_live_image)
st.daemon = True
st.start()
 
#Update live image feed
et = threading.Thread(target=update_predict_image)
et.daemon = True
et.start()

det = threading.Thread(target=run_detection)
det.daemon = True
det.start()

s4 = threading.Thread(target=start_conv)
s4.daemon = True
s4.start()

 
#=================================================================================================
top.mainloop()  

