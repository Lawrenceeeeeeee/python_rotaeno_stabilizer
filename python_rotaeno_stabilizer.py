import cv2
import numpy as np
from tqdm import tqdm
import glob
import os
import subprocess
import time


def add_audio_to_video(video_file, audio_source, output_file):
    command = [
        'ffmpeg',
        '-i', video_file,  # 输入的视频文件
        '-i', audio_source,  # 输入的音频来源文件
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-strict', 'experimental',
        output_file  # 输出的文件名
    ]
    subprocess.call(command)


def find_mp4_videos():
    dir = os.path.join(os.getcwd(), 'videos')  # 指向videos目录
    videos = []
    for file_path in glob.glob(os.path.join(dir, '*.mp4')):
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, dir)
            videos.append(relative_path)
    return videos


def compute_rotation(left_color, right_color, center_color, sample_color):
    OffsetDegree = 180.0

    centerDist = np.linalg.norm(np.array(center_color) - np.array(sample_color))
    leftLength = np.linalg.norm(np.array(left_color) - np.array(center_color))
    leftDist = np.linalg.norm(np.array(left_color) - np.array(sample_color))
    rightDist = np.linalg.norm(np.array(right_color) - np.array(sample_color))

    dir = -1 if leftDist < rightDist else 1
    if leftLength == 0:
        angle = OffsetDegree  # 或其他合适的默认值
    else:
        angle = (centerDist - leftLength) / leftLength * 180.0 * dir + OffsetDegree

    # 注意，如果旋转方向是相反的，只需返回-angle即可
    return -angle


# 识别目录中的视频
# mp4_videos = find_mp4_videos()
# print(mp4_videos)
# quit()
def render(video):
    video_dir = os.path.join(os.getcwd(), 'videos', video)
    video_file_name = os.path.basename(video)  # 获取不带路径的文件名
    video_name = os.path.splitext(video_file_name)[0]
    print(video_name)
    print(video_file_name)
    cap = cv2.VideoCapture(video_dir)
    # fps = round(cap.get(cv2.CAP_PROP_FPS), 2)
    fps = cap.get(cv2.CAP_PROP_FPS)
    print("fps:", fps)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    output_path = os.path.join(os.getcwd(), 'output', f'{video_name}_stb.mp4')  # 指定输出路径
    out = cv2.VideoWriter(output_path, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # 使用tqdm展示进度
    for _ in tqdm(range(frame_count), desc="Processing video"):
        ret, frame = cap.read()
        if ret:
            height, width, channels = frame.shape

            # Sample colors
            O = 5
            S = 3
            sampleColor = frame[height - O:height - O + S, O:O + S].mean(axis=(0, 1))
            leftColor = frame[O:O + S, O:O + S].mean(axis=(0, 1))
            rightColor = frame[height - O:height - O + S, width - O:width - O + S].mean(axis=(0, 1))
            centerColor = frame[O:O + S, width - O:width - O + S].mean(axis=(0, 1))

            angle = compute_rotation(leftColor, rightColor, centerColor, sampleColor)

            # Rotate frame
            M = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
            rotated_frame = cv2.warpAffine(frame, M, (width, height))

            out.write(rotated_frame)
            # time.sleep(1 / fps)
        else:
            print("Error reading frame")

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # 用这个方法添加音频，但是目前视频时长不匹配，会导致音画不同步(需要安装ffmpeg)
    # add_audio_to_video(f'{video_name}_stb.mp4', video, f'{video_name}_with_audio.mp4')