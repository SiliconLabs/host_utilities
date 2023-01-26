# Memory LCD converter utility

The SHARP memory LCDs used on Silab's development kits use a non standard image format. This python script serves to easily convert common image formats to bitmap buffers so that they can be used in your project with the [GLIB Graphics Library](https://docs.silabs.com/gecko-platform/3.2/middleware/api/group-glib).

- [Requirements](#requirements)
- [Usage](#usage)
- [Background Information](#background-information)
  - [1-bit (B/W)](#1-bit-bw)
  - [3-bit (RGB)](#3-bit-rgb)
- [Resources](#resources)

## Requirements

Python v3.6+ is required for this utility. You can check your python installation version with the following command

```
$ python --version
```

Some systems with multiple python installations

```
$ python3 --version
```

This utility uses the Python Imaging Library to process common image formats into compatible buffers for the memory LCDs. To ensure all required dependencies are installed run the following:

```
$ pip install -r requirements.txt
```

## Usage

```
$ python img_to_memlcd.py image.png
```

A folder is generated based on the name of the image file and it contains two header files, one for color and one for b/w, which are the byte buffer representation usable with GLIB's [GLIB_drawBitmap()](https://docs.silabs.com/gecko-platform/3.2/middleware/api/group-glib#ga7f842e14d1302ea20a2ffffaeef19f27) api.

```
.
├── image
│   ├── image_color.h
│   └── image_mono.h
├── img_to_memlcd.py
└── README.md
```

Optional Arguments
```
usage: img_to_memlcd.py [-h] [-v] [-x WIDTH] [-y HEIGHT] [-r] path

positional arguments:
  path                  relative path to image file

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         saves all conversion results
  -x WIDTH, --width WIDTH
                        max width of image
  -y HEIGHT, --height HEIGHT
                        max height of image
  -r, --ratio           keep aspect ratio of original image on resize
```

## Background Information

The SHARP memory LCD updates by line so the data sent has a minimum size dependent on the horizontal resolution of the screen. There are two display variants found on Silicon Lab's Development Kits, [1-bit black and white](#1-bit-bw) and [3-bit color](#3-bit-rgb).

### 1-bit (B/W)

[LS013B7DH03](https://www.sharpsde.com/fileadmin/products/Displays/Specs/LS013B7DH03_25Apr16_Spec_LD-28410A.pdf)

This monochrome display uses 1-bit to represent a pixel. Thus, one byte contains 8 pixels worth of information. To draw one line of a 128 x 128 b/w display would require `128 (pixels) * 1 (bit/pixel) / 8 (bits/byte) = 16 bytes`.

### 3-bit (RGB)

[LS013B7DH06](https://media.digikey.com/pdf/Data%20Sheets/Sharp%20PDFs/LS013B7DH06_Spec.pdf)

This color display uses 3-bits to represent a pixel. Since data is written to the display by line, data is packed left most pixel first in little-endian format. For example, consider 3 pixels {R, G, B}. Then the binary representation would be as follows:

```
+-+-+-+-+-+-+-+-+-+-+
|0 0 1 0 1 0 1 0| | 0
+-+-+-+-+-+-+-+-+-+-+
 pix0 | pix1|  pix2 |
```

To draw one line of a 128 x 128 color display would require `128 (pixels) * 3 (bits/pixel) / 8 (bits/byte) = 48 bytes`


## Resources

- [Sharp Memory LCDs Programming Application Note](https://www.sharpsde.com/fileadmin/products/Displays/2016_SDE_App_Note_for_Memory_LCD_programming_V1.3.pdf)
- [Python Image Library](https://pillow.readthedocs.io/en/stable/)
- [Color Bit Exploration](https://rgbtohex.page/models/color-bit-depth)

