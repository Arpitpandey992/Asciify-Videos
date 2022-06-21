import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import ffmpeg
import os
import sys


class Ascify():

    def __init__(self, charArray, font, fontSize):
        self.charArray = charArray
        self.font = ImageFont.truetype(font, size=fontSize)

    def ShowImg(self, image, pil=False):
        cv2_img = image
        if pil:
            cv2_img = self.PIL2CV2(image)

        cv2.namedWindow("output", cv2.WINDOW_NORMAL)
        cv2.imshow('output', cv2_img)
        cv2.waitKey(0)

    def PIL2CV2(self, image):
        cv2_img = np.array(image)
        if(len(cv2_img.shape) == 3):
            cv2_img = cv2.cvtColor(cv2_img, cv2.COLOR_RGB2BGR)
        return cv2_img

    def AscifyImage(self, image, bg="black", res=-1, save=False, show=False):
        BGCode = 0
        if bg == "white":
            BGCode = 255
        imageHeight, imageWidth, _ = image.shape
        fontWidth, fontHeight = self.font.getsize("$")
        # Resizing the image if it's asked, or when the dimentions are not even (gives problems with ffmpeg)
        if res == -1 and (imageHeight % 2 != 0 or imageWidth % 2 != 0):
            res = imageWidth
        if res != -1:
            scale = imageWidth/res
            imageWidth = res
            imageHeight = int(imageHeight/scale)
            # FFmpeg gives error when height or width is not divisible by 2, so reducing height/width by one pixel if they are odd
            if imageWidth % 2 != 0:
                imageWidth -= 1
            if imageHeight % 2 != 0:
                imageHeight -= 1
            image = cv2.resize(image, (imageWidth, imageHeight))
        RGBImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        HSVImage = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # LabImage = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        output = np.full_like(image, BGCode)
        PILOutput = Image.fromarray(output)
        PILDrawer = ImageDraw.Draw(PILOutput)

        numRows = int(imageHeight / fontHeight)
        numCols = int(imageWidth / fontWidth)
        for i in range(numRows):
            for j in range(numCols):
                x1 = fontWidth*j
                y1 = fontHeight*i
                x2 = fontWidth*(j+1)
                y2 = fontHeight*(i+1)

                #Calculating Intensity Using Lab Image:
                # intensity = np.mean(LabImage[y1:y2, x1:x2, 0])

                #Calculating Intensity Using HSV Image:
                i1 = np.mean(HSVImage[y1:y2, x1:x2, 1])
                i2 = np.mean(HSVImage[y1:y2, x1:x2, 2])
                intensity = (i1 + i2)/2

                #Calculating intensity Using RGB Image:
                # g = np.mean(image[y1:y2, x1:x2, 0])
                # b = np.mean(image[y1:y2, x1:x2, 1])
                # r = np.mean(image[y1:y2, x1:x2, 2])
                # intensity = (r+g+b)/3
    
                position = int((intensity/255) * (len(self.charArray)-1))

                color = np.mean(RGBImage[y1:y2, x1:x2],
                                axis=(0, 1)).astype(np.uint8)

                PILDrawer.text((x1, y1), str(
                    self.charArray[position]), font=self.font, fill=tuple(color))

        output = np.array(PILOutput)
        HSVOutput = cv2.cvtColor(output, cv2.COLOR_RGB2HSV)
        # increasing the Brightness by 20
        for r in HSVOutput:
            for c in r:
                c[2] = min(255, c[2]+20)
        BGROutput = cv2.cvtColor(HSVOutput, cv2.COLOR_HSV2BGR)
        if save:
            cv2.imwrite("./Outputs/Out.png", BGROutput)
        if show:
            self.ShowImg(BGROutput)
        return BGROutput

    def AsciifyVideo(self, video_path, bg="black", frame_skip=1, res=-1):
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
        idx = 1
        for frame_idx in range(NumFrames):
            # Reading a frame
            ret, frame = vidCap.read()
            if ret == False:
                break
            if frame_idx % frame_skip != 0:
                continue
            cv2.imwrite(f"{path_frames}/frame_{idx}.png",
                        self.AscifyImage(frame, bg=bg, res=res))
            print(f"Processed Frame : {frame_idx}")
            idx += 1
        print("Done Processing Frames")

        # Assembling Video from the Produced Frames and Audio from the input Video
        in1 = ffmpeg.input(f'{path_frames}/frame_%d.png',
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


def main():
    charArray = " .'`^\",:;Il!i<~+_-?[{1(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
    font = "fonts/DejaVuSansMono-Bold.ttf"
    fontSize = 8
    ascifyObj = Ascify(charArray, font, fontSize)
    # arguments - FilePath, FileType, Resolution, FrameSkip, Background Color
    args = ["data/Videos/Video_Sample.mp4", "-v", -1, 1, "black"]
    for i in range(1, len(sys.argv)):
        args[i-1] = sys.argv[i]
    if args[1] == '-v':
        ascifyObj.AsciifyVideo(
            args[0], res=int(args[2]), frame_skip=int(args[3]), bg=args[4])
    elif args[1] == '-i':
        ascifyObj.AscifyImage(cv2.imread(args[0]), res=int(args[2]),
                              bg=args[4], show=True, save=True)
    # ascifyObj.AscifyImage(cv2.imread('data/Images/Arch-linux-logo.png'), res=400,
    #                       bg="black", show=True, save=True)


if __name__ == "__main__":
    main()
