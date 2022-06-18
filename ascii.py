import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFont
import ffmpeg
import os

def ShowImg(image, pil=False):
    cv2_img = image.copy()
    if pil:
        cv2_img = PIL2CV2(image)

    cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    cv2.imshow('output', cv2_img)
    cv2.waitKey(0)


def PIL2CV2(image):
    cv2_img = np.array(image)
    if(len(cv2_img.shape) == 3):
        cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_RGB2BGR)
    return cv2_img


def AscifyImage(image, bg="black", res=-1, save=False, show=False):
    if bg == "white":
        bg_code = 255
    elif bg == "black":
        bg_code = 0
    image_height, image_width, _ = image.shape
    # Resizing the image if it's asked, or when the dimentions are not even (gives problems with ffmpeg)
    if res == -1 and (image_height % 2 != 0 or image_width % 2 != 0):
        res = image_width
    if res != -1:
        scale = image_width/res
        image_width = res
        image_height = int(image_height/scale)
        # FFmpeg gives error when height or width is not divisible by 2, so reducing height/width by one pixel if they are odd
        if image_width % 2 != 0:
            image_width -= 1
        if image_height % 2 != 0:
            image_height -= 1
        image = cv2.resize(image, (image_width, image_height))
    font_width, font_height = font.getsize("A")
    lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # hsv_image[..., 1] = cv2.equalizeHist(hsv_image[..., 1])
    # hsv_image[..., 2] = cv2.equalizeHist(hsv_image[..., 2])

    rgb_image = cv2.cvtColor(hsv_image, cv2.COLOR_HSV2RGB)

    output = np.full_like(image, bg_code)
    pillow_output = Image.fromarray(output)
    pillow_drawer = ImageDraw.Draw(pillow_output)
    num_rows = int(image_height / font_height)
    num_cols = int(image_width / font_width)

    for i in range(num_rows):
        for j in range(num_cols):
            y_start = font_height*i
            x_start = font_width*j
            y_end = font_height*(i+1)
            x_end = font_width*(j+1)

            # intensity = np.mean(lab_image[y_start:y_end, x_start:x_end, 0])
            i1 = np.mean(hsv_image[y_start:y_end, x_start:x_end, 1])
            i2 = np.mean(hsv_image[y_start:y_end, x_start:x_end, 2])
            intensity = (i1 + i2)/2
            # g = np.mean(image[y_start:y_end, x_start:x_end, 0])
            # b = np.mean(image[y_start:y_end, x_start:x_end, 1])
            # r = np.mean(image[y_start:y_end, x_start:x_end, 2])
            # intensity = (r+g+b)/3
            # intensity = 233

            position = int((intensity/255) * (len(char_list)))-1

            color = np.mean(rgb_image[y_start:y_end, x_start:x_end], axis=(
                0, 1)).astype(np.uint8)
            # color = (255, 255, 255)

            pillow_drawer.text((x_start, y_start), str(
                char_list[position]), font=font, fill=tuple(color))

    output = np.array(pillow_output)
    output_hsv = cv2.cvtColor(output, cv2.COLOR_RGB2HSV)
    # output_hsv[..., 1] = cv2.equalizeHist(output_hsv[..., 1])
    # output_hsv[..., 2] = cv2.equalizeHist(output_hsv[..., 2])
    # increasing the Brightness by 20
    for r in output_hsv:
        for c in r:
            c[2] = min(255, c[2]+20)
    output_bgr = cv2.cvtColor(output_hsv, cv2.COLOR_HSV2BGR)
    if save:
        cv2.imwrite("./Outputs/Out.png", output_bgr)
    if show:
        ShowImg(output_bgr)
    return output_bgr


def AsciifyVideo(video_path, background="black", frame_skip=1, resolution=-1):
    # Building the File Path for the Output
    out_path = './Outputs'
    file_name = os.path.splitext(os.path.basename(video_path))[0]
    in_extension = os.path.splitext(os.path.basename(video_path))[1]
    path = os.path.join(out_path, file_name)
    path_frames = os.path.join(path, 'frames')
    os.makedirs(path_frames, mode=0o777, exist_ok=True)

    # Capturing the Video And Extracting Frames
    vidCap = cv2.VideoCapture(video_path)
    NumFrames = int(vidCap.get(cv2.CAP_PROP_FRAME_COUNT))
    FPS = vidCap.get(cv2.CAP_PROP_FPS)
    for frame_idx in range(NumFrames):
        # Reading a frame
        ret, frame = vidCap.read()
        if ret == False:
            break
        if frame_idx % frame_skip != 0:
            continue
        cv2.imwrite(f"{path_frames}/frame_{frame_idx+1}.jpg",
                    AscifyImage(frame, bg=background, res=resolution))
        print(f"Processed Frame : {frame_idx}")
    print("Done Processing Frames")

    # Assembling Video from the Produced Frames and Audio from the input Video
    in1 = ffmpeg.input(f'{path_frames}/frame_%d.jpg',
                       framerate=(FPS/frame_skip))
    # Checking if audio is present in original stream
    audio_present = ffmpeg.probe(video_path, select_streams='a')
    if audio_present['streams']:
        in2 = ffmpeg.input(video_path)
        ffmpeg.concat(in1.video, in2.audio, v=1, a=1).output(
            f'{path}/{file_name}{in_extension}').run()
    else:
        in1.output(f'{path}/{file_name}{in_extension}').run()

    # Cleaning up
    vidCap.release()
    cv2.destroyAllWindows()


char_list = " .'`^\",:;Il!i<~+_-?[{1(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
font = ImageFont.truetype("fonts/DejaVuSansMono-Bold.ttf", size=10)
# AscifyFrame(image=cv2.imread(
#     "/home/arpit/Pictures/Wallpapers/11chromaticdark.png"), bg="black")

# AsciifyVideo('/home/arpit/Programming/Python/ASCII-Art-Gen/Asciify-Videos/data/Video_Sample.mp4',
#              background="black", resolution=500)
# AscifyImage(cv2.imread("data/Images/arch-linux-wallpaper-1080p.png"),
#             bg="black", save=True, show=False)
AscifyImage(cv2.imread("data/Images/Umineko_Ricordando_il_Passato.jpg"),
            bg="white", res=1920, save=True, show=False)
# AscifyImage(cv2.imread(
#     "data/input2.jpg"), bg="white", save=True, show=False)
# AscifyImage(cv2.imread(
#     "/home/arpit/Programming/Python/ASCII-Art-Gen/data/python-logo.png"), save=True, show=False)
