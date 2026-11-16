import struct, sys
from PIL import Image
def load(path):
    b = open(path,'rb').read()
    assert b[:4] == b'RB12'
    maxw, h, asc, depth = struct.unpack_from('<4H', b, 4)
    first, default, size, bits_size, noff, nwid = struct.unpack_from('<6I', b, 12)
    p = 36
    bits = b[p:p+bits_size]; p += bits_size
    if noff:
        if bits_size < 0xFFDB:
            if p & 1: p += 1
            offs = struct.unpack_from('<%dH' % noff, b, p); p += 2*noff
        else:
            while p & 3: p += 1
            offs = struct.unpack_from('<%dI' % noff, b, p); p += 4*noff
    else: offs = None
    wids = b[p:p+nwid] if nwid else None
    return dict(maxw=maxw,h=h,asc=asc,depth=depth,first=first,default=default,size=size,bits=bits,offs=offs,wids=wids,end=p+nwid,total=len(b))
def glyph(f, ch):
    i = ord(ch) - f['first']
    w = f['wids'][i] if f['wids'] else f['maxw']
    o = f['offs'][i] if f['offs'] else i * ((f['h']*w+1)//2)
    h = f['h']; im = Image.new('L', (max(w,1), h), 255)
    for y in range(h):
        for x in range(w):
            n = y*w + x
            byte = f['bits'][o + n//2]
            v = (byte >> 4) if (n & 1) else (byte & 15)
            im.putpixel((x,y), v*17)
    return im
if __name__ == '__main__':
    f = load(sys.argv[1])
    print({k:v for k,v in f.items() if k not in('bits','offs','wids')}, 'offs16' if f['bits'] and len(f['bits'])<0xFFDB else 'offs32')
    s = sys.argv[2]
    ims = [glyph(f,c) for c in s]
    W = sum(i.width for i in ims); out = Image.new('L',(W, f['h']),255); x=0
    for i in ims: out.paste(i,(x,0)); x+=i.width
    out.resize((W*4, f['h']*4), Image.NEAREST).save(sys.argv[3])
