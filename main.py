import glob
import os
import time

from python_rotaeno_stabilizer import RotaenoStabilizer

def find_all_videos():
    """
    寻找videos目录下的所有视频文件，不区分大小写
    :return: 视频列表
    """
    dir = os.path.join(os.getcwd(), 'videos')  # 指向videos目录
    videos = []
    # 包括每种格式的大写和小写版本
    video_formats = ['*' + ext for ext in RotaenoStabilizer.format_to_fourcc.keys()]
    video_formats += ['*' + ext.upper() for ext in RotaenoStabilizer.format_to_fourcc.keys()]  # 添加大写格式

    for video_format in video_formats:
        for file_path in glob.glob(os.path.join(dir, video_format)):
            if os.path.isfile(file_path):
                relative_path = os.path.relpath(file_path, dir)
                videos.append(relative_path)

    return videos



if __name__ == '__main__':
    videos = find_all_videos()
    print(videos)
    for video in videos:
        start = time.time()
        try:
            print("正在处理:", video)
            if video[0:2] == "v1":
                stab_task = RotaenoStabilizer(video, type="v1")
            else:
                stab_task = RotaenoStabilizer(video)

            stab_task.run()
        except Exception as e:
            print("处理视频时发生错误:", e)
        end = time.time()
        print(f"用时：{end - start}s")

# if __name__ == '__main__':
#     videos = find_all_videos()
#     print(videos)
#     for video in videos:
#         start = time.time()
#         print("正在处理:", video)
#         if video[0:2] == "v1":
#             stab_task = RotaenoStabilizer(video, type="v1")
#         else:
#             stab_task = RotaenoStabilizer(video)
#
#         stab_task.run()
#
#         end = time.time()
#         print(f"用时：{end - start}s")