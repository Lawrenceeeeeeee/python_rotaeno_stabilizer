# Python Rotaeno Stabilizer (English README)

*阅读 [中文版](README.md).*

This is a Python-based Rotaeno screen recording stabilization script. Its principle is the same as the script provided by Rotaeno for Adobe After Effects, which rotates frames based on the colors of the four corners of the screen recording in live broadcast mode. The goal is to stabilize the video image.

## Features

- No need to install Adobe After Effects; rendering can be done with just one command.
- Supports batch processing of videos.

## Installation

1. Download the project code:
```shell
git clone https://github.com/Lawrenceeeeeeee/python_rotaeno_stabilizer.git
```
Alternatively, you can directly click "Download ZIP" on this repository page, then unzip the downloaded file.

2. Install the dependencies:
```shell
# Navigate to the directory containing the script
cd python_rotaeno_stabilizer
pip install -r requirements.txt
```

## How to Use

0. Important!!! Before recording, please enable "Streaming Mode" in Rotaeno's settings. After enabling, color blocks that record device rotation angles will appear at the four corners of the screen.

1. Place the videos you want to process in the project directory.

2. Run the project:
```shell
python main.py
```

## Known Issues
- Even though the rendered video has the same frame count and frame rate as the original video, there is still a difference in video duration. Currently, this issue remains unresolved. As a result, videos produced by this project temporarily do not have audio and can only be stretched and synced in editing software. If you have a solution, feel free to fork this project and submit your changes.