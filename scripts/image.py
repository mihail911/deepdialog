import numpy as np
from PIL import Image, ImageDraw, ImageFont

default_font = ImageFont.truetype("arial.ttf", size=15)

class ImageMaker(object):
    w=None
    s=None
    grayscalecolors=None

    
    def __init__(self, width, padding, colors=[255,32,128]):
        self.w = width
        self.s = padding
        self.grayscalecolors = np.array(colors,dtype=np.dtype(np.uint8))

    def make_block(self):
        s = self.s
        w = self.w
        b = np.full((w+2*s, w+2*s), 2, dtype=np.dtype(np.int32))
        b[s:s+w,s:s+w] = 1
        return b

    def make_nonblock(self):
        s = self.s
        w = self.w
        b = np.full((w+2*s, w+2*s), 2, dtype=np.dtype(np.int32))
        b[s:s+w,s:s+w] = 0
        return b

    def make_image_array(self,bitmap):
        squares = [self.make_nonblock(), self.make_block()]
        rows = []
        for i in range(bitmap.shape[0]):
            rows.append(np.hstack([squares[k] for k in list(bitmap[i])]))
        return np.vstack(rows)

    def save_bitmap(self, bitmap, outfile, ordered_actions):
        img_array = self.make_image_array(bitmap)
        grayscale = self.grayscalecolors[img_array.astype(np.uint8)]
        image = Image.fromarray(grayscale)
        draw = ImageDraw.Draw(image)
        for (idx,position) in enumerate(ordered_actions):
            row = position[0]
            col = position[1]
            top_left_xdim = col * (self.w + self.s) + 1 + self.w/2
            top_left_ydim = row * (self.w + self.s) + 1 + self.w/2
            draw.text((top_left_xdim, top_left_ydim), str(idx+1), fill=(255, 255, 255), font=default_font)
        image.save(outfile)
