import cv2
import threading
import pyautogui
import numpy as np
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse

app = FastAPI()
frame_lock = threading.Lock()
latest_frame = None

def screen_capture():
    global latest_frame
    screen_width, screen_height = pyautogui.size()
    scaling_factor = 1
    while True:
        img = pyautogui.screenshot(region=(
            0, 
            0, 
            int(screen_width * scaling_factor), 
            int(screen_height * scaling_factor)))
        with frame_lock:
            latest_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def is_duplicate_frame(current_frame, prev_frame, threshold=5):
    """检测重复帧：像素差异小于阈值视为重复"""
    if prev_frame is None:
        return False
    # 灰度计算
    current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    diff = cv2.absdiff(current_gray, prev_gray)
    return np.mean(diff) < threshold

def is_black_screen(frame, threshold=15):
    """检测黑屏：平均亮度小于阈值视为黑屏"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return np.mean(gray) < threshold

@app.get('/video_feed')
def video_feed(quality: int = 70, fps: int = 25, diff_threshold: int = 5, brightness_threshold: int = 15):
    """实时视频流接口
    - quality: JPEG质量 (1-100)
    - fps: 目标帧率
    - diff_threshold: 帧差异阈值（0-255）
    - brightness_threshold: 黑屏亮度阈值（0-255）
    """
    def generate():
        prev_valid_frame = None
        while True:
            with frame_lock:
                current_frame = latest_frame.copy() if latest_frame is not None else None
            
            if current_frame is None:
                continue
                
            if is_black_screen(current_frame, brightness_threshold):
                threading.Event().wait(1/fps)
                continue
                
            if is_duplicate_frame(current_frame, prev_valid_frame, diff_threshold):
                threading.Event().wait(1/fps)
                continue
                
            prev_valid_frame = current_frame
            _, jpeg = cv2.imencode('.jpg', current_frame, 
                [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            
            threading.Event().wait(1/fps)

    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame',
        headers={
            'X-FrameRate': str(fps),
            'X-Resolution': '2560x1600'
        }
    )

if __name__ == '__main__':
    threading.Thread(target=screen_capture, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
