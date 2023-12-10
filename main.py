import glob
import os
import time

from python_rotaeno_stabilizer import RotaenoStabilizer as rs


def find_mp4_videos():
    """
    寻找videos目录下的全部mp4文件
    :return: 视频列表
    """
    dir = os.path.join(os.getcwd(), 'videos')  # 指向videos目录
    videos = []
    for file_path in glob.glob(os.path.join(dir, '*.mp4')):
        if os.path.isfile(file_path):
            relative_path = os.path.relpath(file_path, dir)
            videos.append(relative_path)
    return videos


if __name__ == '__main__':
    videos = find_mp4_videos()
    print(videos)
    for video in videos:
        start = time.time()
        try:
            print("正在处理:", video)
            if video[0:2] == "v1":
                stab_task = rs(video, type="v1")
            else:
                stab_task = rs(video)

            stab_task.run()
        except Exception as e:
            print("处理视频时发生错误:", e)
        end = time.time()
        print(f"用时：{end - start}s")
