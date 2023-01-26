'''
***************************************************************************//**
* @file img_to_memlcd.py
* @brief Utility script to convert images to data format for Sharp LCDs
* @version 1.0
*******************************************************************************
* # License
* <b>Copyright 2020 Silicon Laboratories Inc. www.silabs.com</b>
*******************************************************************************
*
* SPDX-License-Identifier: Zlib
*
* The licensor of this software is Silicon Laboratories Inc.
*
* This software is provided \'as-is\', without any express or implied
* warranty. In no event will the authors be held liable for any damages
* arising from the use of this software.
*
* Permission is granted to anyone to use this software for any purpose,
* including commercial applications, and to alter it and redistribute it
* freely, subject to the following restrictions:
*
* 1. The origin of this software must not be misrepresented; you must not
*    claim that you wrote the original software. If you use this software
*    in a product, an acknowledgment in the product documentation would be
*    appreciated but is not required.
* 2. Altered source versions must be plainly marked as such, and must not be
*    misrepresented as being the original software.
* 3. This notice may not be removed or altered from any source distribution.
*
*******************************************************************************
* # Experimental Quality
* This code has not been formally tested and is provided as-is. It is not
* suitable for production environments. In addition, this code will not be
* maintained and there may be no bug maintenance planned for these resources.
* Silicon Labs may update projects from time to time.
******************************************************************************/
'''

# image manipulation imports
from PIL import Image

# utility imports
import argparse
import tempfile
import atexit
import string
import re

# system imports
from os import path
import shutil
import sys
import io
import os

# debugging imports
import logging


image_path = ""

# c header file template path
_template_path = "header_template.txt"

# global variables to reference image properties
img_name: str
frame_count: int
temp_path: str

def setup(verbose: bool):
    """Creates temporary directories and initializes logging"""
    
    global temp_path

    # create output directory
    if path.exists(img_name):
        shutil.rmtree(img_name)    
        
    os.mkdir(img_name)


    # temporary directory for script operation
    if not verbose:
        temp_path = tempfile.mkdtemp()
    else:
        temp_path = img_name

    # create logging instance
    if verbose:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stderr, level=logging.CRITICAL)

    logging.debug("temp_path: {}".format(temp_path))

    # create temporary directories to store conversion results
    shutil.rmtree(path.join(temp_path, "resize"), ignore_errors=True)
    shutil.rmtree(path.join(temp_path, "color"), ignore_errors=True)
    shutil.rmtree(path.join(temp_path, "mono"), ignore_errors=True)

    os.mkdir(path.join(temp_path, "resize"))
    os.mkdir(path.join(temp_path, "color"))
    os.mkdir(path.join(temp_path, "mono"))

def cleanup(verbose: bool):
    """tears down script requirements"""

    if not verbose:
        shutil.rmtree(temp_path)


def image_read(image_path: str, size: tuple, ratio: bool) -> tuple:
    """Resizes and converts common image formats into 128x128 bitmaps"""
    
    # link global vars
    global frame_count

    actual_size = ()

    logging.debug("img_name: {}".format(img_name))

    # Use Pillow to read image
    with Image.open(image_path) as img:
        frame_count = img.n_frames
        
        # for each frame of the image (gifs) resize and convert to bitmap
        for frame in range(frame_count):
            img.seek(frame)

            if ratio:
                img.thumbnail(size)
                res = img.copy()
            else:
                res = img.resize(size)

            actual_size = (res.width, res.height)

            res = res.convert("RGB")
            res.save(path.join(temp_path, "resize/{}_{:03d}.bmp".format(img_name, frame)), format='BMP')
    
    return actual_size


def bmp_to_color(bmp: Image) -> Image:
    """Converts Bitmap to psuedo 3-bit indexed color representation"""

    # byte buffer for converted pixel data
    color_data = []

    # each pixel gets converted to 3-bit color representation in 16-bit mode 
    for r, g, b in list(bmp.getdata()):
        red = 255 if r > 127 else 0
        green = 255 if g > 127 else 0
        blue = 255 if b > 127 else 0

        pixel = [red, green, blue]

        color_data.extend(pixel)

    # create new image object from byte buffer
    color = Image.frombytes('RGB', bmp.size, bytes(color_data))

    return color


def bmp_to_mono(bmp: Image) -> Image:
    """Converts Bitmap to 1-bit mono representation in 16-bit mode"""

    # converts to greyscale, then maps to either fully white or fully black
    mono = bmp.convert('L').point(lambda x: 255 if x > 60 else 0, '1')

    return mono


def bmp_to_buffer(bmp: Image) -> list:
    """Forms in-memory byte buffer representation of the bitmap"""

    bitstring = ""

    # due to expected format of display buffer needs to reversed in memory
    img_arr = list(bmp.getdata())
    img_arr.reverse()

    # determines if the bmp is color based on data length of one pixel
    color = isinstance(img_arr[0], tuple)

    if color:
        for r, g, b in img_arr:
            bitstring += str("1") if b == 255 else str("0")
            bitstring += str("1") if g == 255 else str("0")
            bitstring += str("1") if r == 255 else str("0")
    else:
        for y in img_arr:
            bitstring += str("1") if y == 255 else str("0")

    # converts string to base_2, 8-bit integers and formats as a list of chars
    byte_buffer = ['0x{:02X}'.format(x) for x in int(bitstring, 2).to_bytes(len(bitstring) // 8, byteorder='little')]

    return byte_buffer
    

def buffer_to_file(byte_buffer: list, color: bool, size: tuple):
    """Creates C header file from byte buffer"""

    # redirects standard output to buffer stream
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout

    # formats byte buffer to aesthetically fit within a 80 character column 
    #   width.
    for buff in byte_buffer:
        print("\t{".expandtabs(4))
        print("\t\t".expandtabs(4), end='')
        for i, byte in enumerate(buff):
            print(byte, end='')
            if (i+1)%12 == 0 and i!=0:
                print(",")
                print("\t\t".expandtabs(4), end='')
            else:
                print(", ", end='')
        print()
        print("\t},".expandtabs(4))

    # stores formated output to be used later
    output = new_stdout.getvalue()

    # restores standard output
    sys.stdout = old_stdout

    # placeholder for template text
    template_text = ""

    # get template from file
    with open(_template_path) as f:
        template_text = f.read()

    # create a templatable object from template string
    template = string.Template(template_text)

    # substitute metadata
    header = template.safe_substitute(
                img_name = img_name + "_" + ("color" if color else "mono"), img_name_caps = (img_name + "_" + ("color" if color else "mono")).upper(),
                frame_count = frame_count,
                buffer_size = int(size[0]*size[1]*(3 if color else 1)/8),
                buffers = output,
                img_width = size[0],
                img_height = size[1])

    # save header file to output folder
    with open("{}/{}_{}.h".format(img_name, img_name, "color" if color else "mono"), 'w') as f:
        f.write(header)

    


if __name__ == '__main__':

    actual_size = None

    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="relative path to image file", type=str)
    parser.add_argument("-v", "--verbose", help="saves all conversion results", action="store_true")
    parser.add_argument("-x", "--width", help="max width of image", default=128,type=int)
    parser.add_argument("-y", "--height", help="max height of image", default=128, type=int)
    parser.add_argument("-r", "--ratio", help="keep aspect ratio of original image on resize", action="store_true")

    args = parser.parse_args()

    image_path = args.path
    verbose = args.verbose
    size = (args.width, args.height)
    ratio = args.ratio

    print(args)

    # parse image name from file path, sanitize to alphanumeric
    img_name = path.splitext(path.basename(image_path))[0]
    img_name = re.sub("[^0-9a-zA-Z]+", "_", img_name)
    
    # create temp directories
    setup(verbose)

    # register exit utility
    atexit.register(cleanup, verbose)

    # image is resized. converted bmp's are saved in temp directory
    try:
        actual_size = image_read(image_path, size, ratio)
    except:
        logging.error("\n\nImage type could not be opened")
        exit()

    # converts resized images to 3-bit color representation
    for f in os.listdir(path.join(temp_path, "resize")):
        if f.endswith(".bmp"):
            with Image.open(path.join(temp_path, "resize", f)) as bmp:
                color = bmp_to_color(bmp)
                color.save(path.join(temp_path, "color", f))


    # converts resized images to 1-bit monochrome
    for f in os.listdir(path.join(temp_path, "resize")):
        if f.endswith(".bmp"):
            with Image.open(path.join(temp_path, "resize", f)) as bmp:
                mono = bmp_to_mono(bmp)
                mono.save(path.join(temp_path, "mono", f))



    # convert to bytestream for 1-bit and store to headerfile template. 
    #   Create 2d array and create define with number of frames.
    byte_buffer = []

    for f in sorted(os.listdir(path.join(temp_path, "mono"))):
        if f.endswith(".bmp"):
            with Image.open(path.join(temp_path, "mono", f)) as bmp:
                bytes = bmp_to_buffer(bmp)
                byte_buffer.append(bytes)

    # saves b/w header file to output directory
    buffer_to_file(byte_buffer, False, actual_size)

    # convert to bytestream for 3-bit and store to headerfile template. 
    #   Create 2d array and create define with number of frames.
    byte_buffer = []

    for f in sorted(os.listdir(path.join(temp_path, "color"))):
        if f.endswith(".bmp"):
            with Image.open(path.join(temp_path, "color", f)) as bmp:
                bytes = bmp_to_buffer(bmp)
                byte_buffer.append(bytes)

    # saves color header file to output directory
    buffer_to_file(byte_buffer, True, actual_size)