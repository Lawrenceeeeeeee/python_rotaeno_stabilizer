from python_rotaeno_stabilizer import *

videos = find_mp4_videos()
print(videos)

if __name__ == '__main__':
    for video in videos:
        try:
            print("正在处理:", video)
            render(video)
        except Exception as e:
            print("处理视频时发生错误:", e)
