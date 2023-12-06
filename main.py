from python_rotaeno_stabilizer import *

videos = find_mp4_videos()
print(videos)

if __name__ == '__main__':
    for video in videos:
        try:
            print("正在处理:", video)
            if video[0:2] == "v1":
                render(video, type="v1")
            else:
                render(video)
        except Exception as e:
            print("处理视频时发生错误:", e)
