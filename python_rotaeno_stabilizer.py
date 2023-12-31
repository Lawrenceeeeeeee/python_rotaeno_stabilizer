import math
import multiprocessing as mp
import os
import queue
import subprocess
import time
from functools import wraps

import cv2
import numpy as np
from tqdm import tqdm


def timer(fn):
    """计算性能的修饰器"""

    @wraps(fn)
    def measure_time(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print(f"@timer: {fn.__name__} took {t2 - t1: .5f} s")
        return result

    return measure_time


class RotaenoStabilizer:
    def __init__(self, video, type="v2", square=True):
        self.video_file = video
        self.type = type
        self.square = square
        self.video_dir = video if os.path.isabs(video) else os.path.join(os.getcwd(), 'videos', video)  # 判断是否为绝对路径
        self.video_file_name = os.path.basename(video)  # 获取不带路径的文件名
        self.video_name = os.path.splitext(self.video_file_name)[0]  # 获取文件名
        self.video_extension = os.path.splitext(self.video_file_name)[1]  # 获取文件后缀
        self.output_path = os.path.join(os.getcwd(), 'output', f'{self.video_name}_stb.mp4')  # 指定输出路径
        self.cfr_output_path = os.path.join(os.getcwd(), 'output', f'{self.video_name}_cfr.mp4')  # 指定输出路径
        cap = cv2.VideoCapture(self.video_dir)
        self.fps = cap.get(cv2.CAP_PROP_FPS)
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        cap.release()

        self.num_cores = os.cpu_count()

    @timer
    def add_audio_to_video(self, verbose=False):
        """
        将音频添加到视频中。

        :param video_file: 输入的视频文件路径。
        :param audio_source: 输入的音频来源文件路径。
        :param output_file: 输出视频文件的路径。
        :param verbose: 是否显示详细的 ffmpeg 输出，默认为 False。
        :return: None
        """
        output_file = f'output/{self.video_name}_with_audio.mp4'
        command = [
            'ffmpeg',
            '-i', self.output_path,  # 输入的视频文件
            '-i', self.video_dir,  # 输入的音频来源文件
            '-c:v', 'copy',  # 复制视频流
            '-c:a', 'aac',  # 使用 AAC 编码音频
            '-strict', 'experimental',
            output_file  # 输出的文件名
        ]

        if not verbose:
            # 抑制 stdout 和 stderr 输出
            with open(os.devnull, 'wb') as devnull:
                subprocess.run(command, stdout=devnull, stderr=devnull)
        else:
            subprocess.run(command)

    @timer
    def convert_vfr_to_cfr(self, verbose=False):
        """
        将可变帧率 (VFR) 视频转换为固定帧率 (CFR) 视频。

        :param verbose: 是否显示详细的 ffmpeg 输出，默认为 False。
        :return: None
        """
        cmd = [
            'ffmpeg',
            '-i', self.video_dir,
            '-vf', f'fps={self.fps}',
            '-c:a', 'copy',  # 复制音频流而不重新编码
            self.cfr_output_path
        ]

        if not verbose:
            # 抑制 stdout 和 stderr 输出
            with open(os.devnull, 'wb') as devnull:
                subprocess.run(cmd, stdout=devnull, stderr=devnull)
        else:
            subprocess.run(cmd)

    # def get_video_duration(self, video_path):
    #     """
    #
    #     :param video_path: 视频路径
    #     :return: 时长
    #     """
    #     cmd = [
    #         'ffprobe',
    #         '-v', 'error',
    #         '-show_entries', 'format=duration',
    #         '-of', 'default=noprint_wrappers=1:nokey=1',
    #         video_path
    #     ]
    #
    #     result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    #     return float(result.stdout)

    def compute_rotation(self, left_color, right_color, center_color, sample_color):
        """
        根据画面四个角的颜色来计算画面旋转角度
        :param left_color:
        :param right_color:
        :param center_color:
        :param sample_color:
        :return: 旋转角度
        """
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

    def compute_rotation_v2(self, top_left_color, top_right_color, bottom_left_color, bottom_right_color):
        '''
        根据画面四个角的颜色来计算画面旋转角度
        :param top_left_color: 左上角的颜色 (RGB)
        :param top_right_color: 右上角的颜色 (RGB)
        :param bottom_left_color: 左下角的颜色 (RGB)
        :param bottom_right_color: 右下角的颜色 (RGB)
        :return: 旋转角度
        '''

        # 将RGB值转换为0或1
        def convert_color_to_binary(color):
            array = [1 if c >= 255 / 2 else 0 for c in color]
            return array[::-1]  # OpenCV的BGR顺序和RGB相反

        # 将四个角的颜色转换为二进制
        binary_top_left = convert_color_to_binary(top_left_color)
        binary_top_right = convert_color_to_binary(top_right_color)
        binary_bottom_left = convert_color_to_binary(bottom_left_color)
        binary_bottom_right = convert_color_to_binary(bottom_right_color)

        # 将二进制颜色值转换为角度
        color_to_degree = (binary_top_left[0] * 2048 + binary_top_left[1] * 1024 + binary_top_left[2] * 512 +
                           binary_top_right[0] * 256 + binary_top_right[1] * 128 + binary_top_right[2] * 64 +
                           binary_bottom_left[0] * 32 + binary_bottom_left[1] * 16 + binary_bottom_left[2] * 8 +
                           binary_bottom_right[0] * 4 + binary_bottom_right[1] * 2 + binary_bottom_right[2])
        rotation_degree = color_to_degree / 4096 * -360

        return -rotation_degree

    def process_frame(self, frame):
        height, width, channels = frame.shape

        # Sample colors
        O = 5
        S = 3
        bottom_left = frame[height - O:height - O + S, O:O + S].mean(axis=(0, 1))
        top_left = frame[O:O + S, O:O + S].mean(axis=(0, 1))
        bottom_right = frame[height - O:height - O + S, width - O:width - O + S].mean(axis=(0, 1))
        top_right = frame[O:O + S, width - O:width - O + S].mean(axis=(0, 1))

        if self.type == 'v2':
            angle = self.compute_rotation_v2(top_left, top_right, bottom_left, bottom_right)
        else:
            angle = self.compute_rotation(top_left, bottom_right, top_right, bottom_left)

        # Rotate frame
        max_size = math.ceil(math.sqrt(width ** 2 + height ** 2))
        if self.square:  # 方形渲染
            # max_size = max(height, width)

            expanded_frame = np.zeros((max_size, max_size, 3), dtype='uint8')
            expanded_frame[(max_size - height) // 2:(max_size - height) // 2 + height,
            (max_size - width) // 2:(max_size - width) // 2 + width] = frame
            M = cv2.getRotationMatrix2D((max_size / 2, max_size / 2), angle, 1)
            rotated_frame = cv2.warpAffine(expanded_frame, M, (max_size, max_size))
        else:
            M = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
            rotated_frame = cv2.warpAffine(frame, M, (width, height))

        return rotated_frame

    def process_video(self, group_number, frame_jump_unit):
        cap = cv2.VideoCapture(self.cfr_output_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_jump_unit * group_number)
        proc_frames = 0
        inter_output_path = os.path.join(os.getcwd(), 'output', "{}.{}".format(group_number, 'mp4'))

        frame_size = math.ceil(math.sqrt(int(cap.get(3)) ** 2 + int(cap.get(4)) ** 2))
        if self.square:  # 方形
            out = cv2.VideoWriter(inter_output_path, self.fourcc, self.fps, (frame_size, frame_size))
        else:
            out = cv2.VideoWriter(inter_output_path, self.fourcc, self.fps, (int(cap.get(3)), int(cap.get(4))))

        while proc_frames < frame_jump_unit:
            ret, frame = cap.read()
            if ret:
                out.write(self.process_frame(frame))
            else:
                print("Error reading frame")
            proc_frames += 1

        cap.release()
        out.release()
        return None

    def concatenate_videos(self, verbose=False):
        # 构建 FFmpeg 命令
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',  # 如果文件名包含特殊字符，需要此选项
            '-i', 'output/intermediate_files.txt',
            '-c', 'copy',  # 使用 'copy' 来避免重新编码
            self.output_path
        ]

        # 执行命令
        if not verbose:
            # 抑制 stdout 和 stderr 输出
            with open(os.devnull, 'wb') as devnull:
                subprocess.run(cmd, stdout=devnull, stderr=devnull)
        else:
            subprocess.run(cmd)

    @timer
    def render(self):
        """
        :return: 无返回值：
        在output文件夹中输出渲染完毕的视频
        """
        cap2 = cv2.VideoCapture(self.cfr_output_path)
        frame_jump_unit = cap2.get(cv2.CAP_PROP_FRAME_COUNT) // self.num_cores  # 每个进程处理的帧数
        cap2.release()

        p = mp.Pool(self.num_cores)
        video_list = range(self.num_cores)
        video_list = [(item, frame_jump_unit) for item in video_list]
        p.starmap(self.process_video, video_list)  # 多进程开始

        intermediate_files = ["{}.{}".format(i, 'mp4') for i in range(self.num_cores)]
        # print(intermediate_files)

        with open("output/intermediate_files.txt", "w") as f:
            for t in intermediate_files:
                f.write("file {} \n".format(t))

        self.concatenate_videos()

        # 删除中间文件
        for f in intermediate_files:
            os.remove(os.path.join(os.getcwd(), 'output', f))
        os.remove("output/intermediate_files.txt")

    def run(self):  # 渲染方形视频
        """
        :return: 无返回值，在output文件夹输出渲染完毕的视频
        """

        cap = cv2.VideoCapture(self.video_dir)

        print("正在将视频转换为CFR视频……")
        self.convert_vfr_to_cfr()
        cap.release()

        # 接下来只处理CFR视频
        self.render()
        self.add_audio_to_video()

        os.remove(self.cfr_output_path)
        os.remove(self.output_path)

        print(f"{self.video_file_name}稳定完成")
