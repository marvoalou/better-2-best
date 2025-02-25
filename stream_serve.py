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
    while True:
        img = pyautogui.screenshot(region=(0, 0, 1920, 1080))
        with frame_lock:
            latest_frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

@app.get('/video_feed')
def video_feed(quality: int = 70, fps: int = 25):
    """实时视频流接口
    - quality: JPEG质量 (1-100)
    - fps: 目标帧率
    """
    def generate():
        while True:
            with frame_lock:
                if latest_frame is not None:
                    _, jpeg = cv2.imencode('.jpg', latest_frame, 
                        [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            threading.Event().wait(1/fps) 

    return StreamingResponse(
        generate(),
        media_type='multipart/x-mixed-replace; boundary=frame',
        headers={'X-FrameRate': str(fps)}
    )

if __name__ == '__main__':
    threading.Thread(target=screen_capture, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
