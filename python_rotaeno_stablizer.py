import cv2
import numpy as np
from tqdm import tqdm

def compute_rotation(left_color, right_color, center_color, sample_color):
    OffsetDegree = 180.0

    centerDist = np.linalg.norm(np.array(center_color) - np.array(sample_color))
    leftLength = np.linalg.norm(np.array(left_color) - np.array(center_color))
    leftDist = np.linalg.norm(np.array(left_color) - np.array(sample_color))
    rightDist = np.linalg.norm(np.array(right_color) - np.array(sample_color))

    dir = -1 if leftDist < rightDist else 1
    angle = (centerDist - leftLength) / leftLength * 180.0 * dir + OffsetDegree

    # 注意，如果旋转方向是相反的，只需返回-angle即可
    return -angle

cap = cv2.VideoCapture('clip.mp4')
fps = round(cap.get(cv2.CAP_PROP_FPS), 2)
print("fps:", fps)
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('clip_stb.mp4', fourcc, fps, (int(cap.get(3)), int(cap.get(4))))

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
    else:
        break

cap.release()
out.release()
cv2.destroyAllWindows()
