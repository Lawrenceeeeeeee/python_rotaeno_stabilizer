# Python Rotaeno Stabilizer

*Read this in [English](README_EN.md)*

![Python Rotaeno Stabilizer](images/cover.jpg)

[视频演示](https://www.bilibili.com/video/BV1bc411f7fK/?share_source=copy_web&vd_source=9e94008dbf76e399a164028430118348)

这是一个基于Python的Rotaeno录屏稳定脚本，原理和Rotaeno官方提供的Adobe After
Effects脚本一样，是基于直播模式下录屏画面四个角的颜色来旋转帧，从而达到稳定视频画面的目的。

# 更新记录

## v1.3
- 新增背景圆圈, 优化画面观感
- 修复了脚本在Windows上运行的一些bug
- 修复了长宽比偏小的录屏无法正常添加背景圆圈的问题
- 新增了对于mov, avi, mkv, wmv, flv格式的支持

## v1.2

- 增加多进程优化

## v1.1

- 增加正方形渲染功能（感谢[@Ki-wimon](https://github.com/Ki-wimon)的PR），脚本默认采用正方形渲染，以最大程度减少画面裁切
- 为`convert_vfr_to_cfr`和`add_audio_to_video`函数增加了verbose=False形参，减少命令行输出的冗余
- 删除中间文件，仅保留最后输出

## v1.0

- 增加了V2矫正方法，脚本默认按照V2来稳定视频，如果有V1矫正的需要，请在视频文件名前面添加"v1"
  字样，脚本将自动切换到V1矫正模式进行稳定，例如：`v1-sample.mp4`。

## 功能特点

- 无需安装Adobe After Effects，一行命令即可渲染完成
- 支持批量处理视频

## 安装

1. 下载项目代码：

```shell
git clone https://github.com/Lawrenceeeeeeee/python_rotaeno_stabilizer.git
```

或者直接在本仓库界面点击Download ZIP下载然后解压

2. 安装依赖：

```shell
# 切换到脚本所在目录
cd python_rotaeno_stabilizer
pip install -r requirements.txt
```

3. 安装FFmpeg

请在[FFmpeg官网](https://ffmpeg.org/download.html)上下载对应的安装包

## 使用方法

0. **注意！！！** 录屏前请在Rotaeno的设置中开启"直播模式"，开启后屏幕的四个角将会出现记录设备旋转角的色块。

1. 将待处理的视频放在`videos`目录下 (目前支持mp4, mov, avi, mkv, wmv, flv)

2. 启动项目：

```shell
python main.py
```

3. 在`output`文件夹找渲染完成的视频

效果如下:

![演示](images/example.gif)

## 联系作者

请在我的[Bilibili账号](https://space.bilibili.com/143784401)下私信我
