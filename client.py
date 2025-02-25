import cv2
import requests
import numpy as np

url = "http://localhost:8000/video_feed?quality=85&fps=240"

def process_stream():
    stream = requests.get(url, stream=True)
    bytes_buffer = bytes()
    for chunk in stream.iter_content(chunk_size=1024):
        bytes_buffer += chunk
        a = bytes_buffer.find(b'\xff\xd8')  
        b = bytes_buffer.find(b'\xff\xd9')  
        if a != -1 and b != -1:
            jpeg = bytes_buffer[a:b+2]
            bytes_buffer = bytes_buffer[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
            
            cv2.imshow('Live Stream', frame)
            if cv2.waitKey(1) == ord('q'):
                break

if __name__ == '__main__':
    process_stream()
