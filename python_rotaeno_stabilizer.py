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
    format_to_fourcc = {
        '.mp4': 'mp4v',
        '.mov': 'avc1',
        '.avi': 'XVID',  # 或 'DIVX'
        '.mkv': 'H264',
        '.wmv': 'WMV1',
        '.flv': 'FLV1'
    }

    def __init__(self, video, type="v2", square=True):
        self.video_file = video
        self.type = type
        self.square = square
        self.video_dir = video if os.path.isabs(video) else os.path.join(os.getcwd(), 'videos', video)  # 判断是否为绝对路径
        self.video_file_name = os.path.basename(video)  # 获取不带路径的文件名
        self.video_name = os.path.splitext(self.video_file_name)[0]  # 获取文件名
        self.video_extension = os.path.splitext(self.video_file_name)[1]  # 获取文件后缀
        self.output_path = os.path.join(os.getcwd(), 'output',
                                        f'{self.video_name}_stb{self.video_extension}')  # 指定输出路径
        self.cfr_output_path = os.path.join(os.getcwd(), 'output',
                                            f'{self.video_name}_cfr{self.video_extension}')  # 指定输出路径
        self.refined_video_path = os.path.join(os.getcwd(), 'output',
                                               f'{self.video_name}_refined{self.video_extension}')
        cap = cv2.VideoCapture(self.video_dir)
        self.fps = cap.get(cv2.CAP_PROP_FPS)

        if self.video_extension.lower() in self.format_to_fourcc:
            self.fourcc = cv2.VideoWriter_fourcc(*self.format_to_fourcc[self.video_extension.lower()])
        else:
            raise ValueError(f"Unsupported video format: {self.video_extension}")
        # self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        cap.release()

        self.num_cores = os.cpu_count() if os.cpu_count() < 61 else 61

    @timer
    def add_audio_to_video(self, input_video=None, audio=None, verbose=False):
        """
        将音频添加到视频中。

        :param input_video: 输入的视频文件路径。如果为 None，则使用实例的 output_path 属性。
        :param audio: 输入的音频来源文件路径。如果为 None，则使用实例的 video_dir 属性。
        :param verbose: 是否显示详细的 ffmpeg 输出，默认为 False。
        :return: None
        """
        if input_video is None:
            input_video = self.output_path
        if audio is None:
            audio = self.video_dir
        output_file = f'output/{self.video_name}_with_audio{self.video_extension.lower()}'
        command = [
            'ffmpeg',
            '-i', input_video,  # 输入的视频文件
            '-i', audio,  # 输入的音频来源文件
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

    def get_video_duration(self, video_path):
        """

        :param video_path: 视频路径
        :return: 时长
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)

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

    @timer
    def improve_video_quality(self, target_bitrate='50M', verbose=False):
        """
        使用FFmpeg提高视频的码率以改善画质。

        参数:
        - target_bitrate: 目标视频码率，例如 '50M' 代表50 Mbps。
        - verbose: 是否显示详细的 ffmpeg 输出，默认为 False。
        """
        # 构建FFmpeg命令
        command = [
            'ffmpeg',
            '-i', self.output_path,  # 输入视频文件
            '-b:v', target_bitrate,  # 设置视频码率
            '-c:v', 'libx264',  # 设置视频编码器为libx264
            '-preset', 'slow',  # 使用slow预设，以提高编码效率，但编码速度较慢
            self.refined_video_path  # 输出视频文件
        ]

        # 根据verbose参数设置输出
        if verbose:
            subprocess.run(command, check=True)
        else:
            # 抑制 stdout 和 stderr 输出
            with open(os.devnull, 'wb') as devnull:
                subprocess.run(command, stdout=devnull, stderr=devnull, check=True)

        if verbose:
            print(f"视频质量改善完成，输出文件已保存至: {self.refined_video_path}")

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
            """
            设手机尺寸为a*b, 长a, 宽b
            判定环内径: (1050**2+888**2)**0.5 1383/888
                l = 1.1824324324 * b
                ((1.1824324324**2+1)**0.5 * height + 7)
            判定环宽度: 14 (1216宽度下是17)
            
            如果录屏的长宽比小于1.7763157895,则将宽度设置成 长度/1.7763157895
            """
            # max_size = max(height, width)
            background_frame = np.zeros((max_size, max_size, 3), dtype='uint8')

            # 在背景上绘制圆环
            real_height = height if width / height >= 1.7763157895 else width / 1.7763157895
            circle_center = (max_size // 2, max_size // 2)
            circle_radius = (1.5574 * real_height) // 2
            circle_thickness = int(3 / 328 * real_height - 46 / 41)  # 圆环的宽度，比如15px
            cv2.circle(background_frame, circle_center, math.ceil(circle_radius), (255, 255, 255),
                       thickness=circle_thickness)

            # 将原始视频帧放置在中间
            expanded_frame = np.zeros((max_size, max_size, 3), dtype='uint8')
            x_offset = (max_size - width) // 2
            y_offset = (max_size - height) // 2
            expanded_frame[y_offset:y_offset + height, x_offset:x_offset + width] = frame

            # 对扩展帧进行旋转
            M = cv2.getRotationMatrix2D((max_size // 2, max_size // 2), angle, 1)
            rotated_frame = cv2.warpAffine(expanded_frame, M, (max_size, max_size))

            # 创建掩码以识别非黑色像素
            _, mask = cv2.threshold(cv2.cvtColor(rotated_frame, cv2.COLOR_BGR2GRAY), 1, 255, cv2.THRESH_BINARY)

            # 使用掩码叠加非黑色像素到背景帧
            background_frame_masked = cv2.bitwise_and(background_frame, background_frame, mask=cv2.bitwise_not(mask))
            rotated_frame_masked = cv2.bitwise_and(rotated_frame, rotated_frame, mask=mask)
            combined_frame = cv2.add(background_frame_masked, rotated_frame_masked)
            return combined_frame
        else:
            M = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
            rotated_frame = cv2.warpAffine(frame, M, (width, height))

        return rotated_frame

    def process_video(self, group_number, frame_jump_unit):
        cap = cv2.VideoCapture(self.cfr_output_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_jump_unit * group_number)
        proc_frames = 0
        inter_output_path = os.path.join(os.getcwd(), 'output',
                                         "{}.{}".format(group_number, f'{self.video_extension.lower()[1:]}'))

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

        intermediate_files = ["{}.{}".format(i, f'{self.video_extension.lower()[1:]}') for i in range(self.num_cores)]
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
        # self.improve_video_quality()
        self.add_audio_to_video()

        os.remove(self.cfr_output_path)
        os.remove(self.output_path)

        print(f"{self.video_file_name}稳定完成")
