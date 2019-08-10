from PIL import Image
import sys

def crop_stuff(im):
    c=im
    w,h=c.size
    dark, light = c.getextrema()
    upperlim = light * h
    left_w, right_w, up_h, down_h = 0, w, 0, h
    for i in range(w):
        if sum([im.getpixel((i,j)) for j in range(h)]) > upperlim-10:
            left_w=i
        else:
            break
    for i in range(w-1,0,-1):
        if sum([im.getpixel((i,j)) for j in range(h)]) > upperlim-10:
            right_w=i
        else:
            break
    upperlim = light*w
    for j in range(h):
        if sum([im.getpixel((i,j)) for i in range(w)]) > upperlim-10:
            up_h = j
        else:
            break
    for j in range(h-1,0,-1):
        if sum([im.getpixel((i,j)) for i in range(w)]) > upperlim-10:
            down_h = j
        else:
            break
    left_w = left_w-10 if left_w>10 else 0
    right_w = right_w+10 if right_w+10<=w else w
    up_h = up_h-10 if up_h>10 else 0
    down_h = down_h+10 if down_h +10<=h else h
    return c.crop((left_w,up_h,right_w,down_h))

def preprocess(im,pageno,default_linenum,lfr):
    # for each line:
     # 1. count range of pixels present
     # 2. if pixel range too short, just continue on.
     # 3. if too few pixels are black, continue
     # 4. if the rate changes from "unaccepted" to "over some threshold" we will mark this.
     # 5. we need to prune furigana: do the crop((entry,0,entry+10,h)) and crop((entry-5,0,entry+10,h))
    print(f"page {pageno}")
    c = crop_stuff(im)
    try:
        dark,light = c.getextrema()
        w,h = c.size
        upperlim = light * h
    except TypeError: # c is None
        return None
    y = [sum([c.getpixel((i,j)) for j in range(h)]) for i in range(w)]
    prev_res = False
    filtered, final, rates = [],[],[]
    # ----- find where to ~~.
    try:
        for i in range(w):
            up,down = 0,h-1
            while up < h and c.getpixel((i,up)) >= light-1:
                up += 1
            while down > 0 and c.getpixel((i,down)) >= light-1:
                down -= 1
            rate = (upperlim - y[i])/(down+1-up)
            rates.append(rate)
            if up + 20 <= down and (prev_res is False) and rate > 1:
                filtered.append(i)
                prev_res = True
            elif rate < 0.1:
                prev_res = False
    except ZeroDivisionError: 
        print(up,down)
        print(len(rates))
        print("If this message is triggered, please report as an issue.")
    for entry in filtered:
        one = crop_stuff(c.crop((entry,0,entry+10,h)))
        two = crop_stuff(c.crop((entry-5,0,entry+10,h)))
        if abs(one.size[1]-two.size[1])<20:
            final.append(entry)
    # ----- line number & linewidth evaluation
    linenum_flag=False
    try:
        for mae,ushiro in zip(final,final[1:]):
            if abs(ushiro-mae-final[1]-final[0]) > 50:
                linenum_flag = True
        if linenum_flag is True:
            linenum = default_linenum
        elif len(final)>1:
            linenum = len(final)
        else:
            linenum = None
    except IndexError:
        print(filtered)
        print("this image isn't text.")
        return None
    try:
        linewidth = lfr*(final[-1]-final[0])/linenum
    except (TypeError,IndexError):
        print(filtered)
        print("this image isn't text.")
        return None
    # ----- filter
    should_we_filter = [True for i in range(w)]
    for entry in final:
        for i in range(int(linewidth)):
            try:
                should_we_filter[entry+i-2] = False
            except IndexError:
                break
    for ind, yes_or_no in enumerate(should_we_filter):
        if yes_or_no is True:
            c.paste(light,box=((ind,0,ind+1,h)))
    return c

def split_into_halves(im,pageno,lines,ratio):
    w,h = im.size
    im = im.crop((w//20,h//11,19*w//20,h))
    w,h = im.size
    im1 = preprocess(im.crop((0,0,w,h//2)),pageno,lines,ratio)
    im2 = preprocess(im.crop((0,h//2,w,h)),pageno,lines,ratio)
    return (im1,im2)

def dont_split_into_halves(im,pageno,lines,ratio):
    w,h  = im.size
    im = im.crop((w//20,h//11,19*w//20,h))
    w,h = im.size
    return preprocess(im,pageno,lines,ratio)

def parse_config(filename):
    ret = {}
    with open(filename,"r") as config:
        lines = config.readlines()
        for line in lines:
            if line[0]=='#':
                continue
            space = line.find(" ")
            word = line[:space]
            if word == "input_digits":
                ret["digits"] = int(line[space+1:]) 
            elif word == "page_start":
                ret["start"] = int(line[space+1:])
            elif word == "page_end":
                ret["end"] = int(line[space+1:])
            elif word == "default_lines":
                ret["dfl"] = int(line[space+1:])
            elif word == "text_chunks":
                ret["chunks"] = int(line[space+1:])
            elif word == "line_furigana_ratio":
                ret["ratio"] = eval(line[space+1:])
            elif word == "output":
                ret["output"] = line[space+1:].replace("{{}}",f"%0{ret['digits']}d").strip() 
            elif word == "input":
                ret["input"] = line[space+1:].replace("{{}}",f"%0{ret['digits']}d").strip()
    return ret

def run(config_file_name):
    d = parse_config(config_file_name)
    for no in range(d["start"],d["end"]+1):
        inputfile = d["input"] % no
        outputfile = d["output"] % no
        try:
            im = Image.open(inputfile)
        except FileNotFoundError:
            print("the file {%s} does not exist" % inputfile)
            continue
        if d["chunks"] == 2:
            (im1,im2) = split_into_halves(im,no,d["dfl"],d["ratio"])
            if im1 is not None:
                im1.save(outputfile.replace(".png","_1.png"))
            if im2 is not None:
                im2.save(outputfile.replace(".png","_2.png"))
        elif d["chunks"] == 1:
            im1 = dont_split_into_halves(im,no,d["dfl"],d["ratio"])
            if im1 is not None:
                im1.save(outputfile)
        else:
            raise Exception("The number of chunks is not 1 or 2.")

if __name__=="__main__":
    try:
        run(sys.argv[1])
    except IndexError:
        print(f"format: python3 {sys.argv[0]} (config file name)")

