import struct
from PIL import Image
def read(path):
    b=open(path,'rb').read()
    off=struct.unpack_from('<I',b,10)[0]; hs=struct.unpack_from('<I',b,14)[0]
    w,h=struct.unpack_from('<ii',b,18); bpp=struct.unpack_from('<H',b,28)[0]
    im=Image.new('RGBA',(w,abs(h)))
    px=im.load()
    if bpp==24:
        row=(w*3+3)&~3
        for y in range(abs(h)):
            r0=off+(abs(h)-1-y)*row
            for x in range(w):
                B,G,R=b[r0+3*x:r0+3*x+3]; px[x,y]=(R,G,B,255)
    elif bpp==32:
        for y in range(abs(h)):
            r0=off+(abs(h)-1-y)*w*4
            for x in range(w):
                B,G,R,A=b[r0+4*x:r0+4*x+4]; px[x,y]=(R,G,B,A)
    return im
