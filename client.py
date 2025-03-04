import cv2
import requests
import numpy as np
import os
from datetime import datetime

url = "http://localhost:8000/video_feed?quality=100&fps=240&width=2560&height=1600"

def process_stream(display_size=(2560, 1600), save_frames=False, save_interval=1, output_dir="captures"):
    """
    增强版视频流处理客户端
    :param display_size: 显示尺寸 (宽, 高)
    :param save_frames: 是否保存帧
    :param save_interval: 保存间隔（每N帧保存一次）
    :param output_dir: 输出目录
    """
    frame_counter = 0
    save_enabled = save_frames
    
    if save_enabled:
        os.makedirs(output_dir, exist_ok=True)
        print(f"帧保存已启用，输出目录：{os.path.abspath(output_dir)}")

    cv2.namedWindow('Live Stream', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Live Stream', *display_size)

    stream = requests.get(url, stream=True)
    bytes_buffer = bytes()
    
    try:
        for chunk in stream.iter_content(chunk_size=1024):
            bytes_buffer += chunk
            a = bytes_buffer.find(b'\xff\xd8')
            b = bytes_buffer.find(b'\xff\xd9')
            
            if a != -1 and b != -1:
                jpeg = bytes_buffer[a:b+2]
                bytes_buffer = bytes_buffer[b+2:]
                
                frame = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
                frame_counter += 1
                
                resized_frame = cv2.resize(frame, display_size, interpolation=cv2.INTER_AREA)
                cv2.imshow('Live Stream', resized_frame)
                
                if save_enabled and frame_counter % save_interval == 0:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = f"frame_{timestamp}_n{frame_counter}.jpg"
                    output_path = os.path.join(output_dir, filename)
                    
                    cv2.imwrite(output_path, frame)
                    print(f"已保存：{filename}", end='\r')
                
                key = cv2.waitKey(1)
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    save_enabled = not save_enabled
                    status = "启用" if save_enabled else "禁用"
                    print(f"\n帧保存状态已切换：{status}")
                    
    finally:
        cv2.destroyAllWindows()
        print("\n视频流处理已终止")

if __name__ == '__main__':
    process_stream(
        display_size=(2560, 1600),
        save_frames=True,
        save_interval=5,  # 240fps时每5帧保存约48fps
        output_dir="screen_captures"
    )
