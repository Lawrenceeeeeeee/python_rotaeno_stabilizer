import time

from python_rotaeno_stabilizer import *

if __name__ == '__main__':
    videos = find_mp4_videos()
    print(videos)
    for video in videos:
        start = time.time()
        try:
            print("正在处理:", video)
            if video[0:2] == "v1":
                multi_render(video, type="v1")
            else:
                multi_render(video)
        except Exception as e:
            print("处理视频时发生错误:", e)
        end = time.time()
        print(f"用时：{end - start}s")
