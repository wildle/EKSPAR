import cv2
import torch
from ultralytics import YOLO
from flask import Flask

print("OpenCV Version:", cv2.__version__)
print("PyTorch Version:", torch.__version__)

model = YOLO("yolov8n.pt") # Testladevorgang für YOLO
print(model)