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
        #        should_we_filter[entry-2] = 2
            except IndexError:
                break
    for ind, yes_or_no in enumerate(should_we_filter):
        if yes_or_no is True:
            c.paste(light,box=((ind,0,ind+1,h)))
        if yes_or_no is 2:
            c.paste(dark,box=((ind,0,ind+1,h)))
    return c

def roll(image,up,down,left,right):
    w,h=image.size
    return image.crop((w*left//100,h*up//100,w-w*right//100,h-h*down//100))

def horizontal_split(image_iter):
    ret = []
    for im in image_iter:
        w,h=im.size
        ret.append(im.crop(w//2,0,w,h))
        ret.append(im.crop(0,0,w//2,h))
    return ret

def vertical_split(image_iter):
    ret = []
    for im in image_iter:
        w,h=im.size
        ret.append(im.crop(0,0,w,h//2))
        ret.append(im.crop(0,h//2,w,h))
    return ret


def into_greyscale(image_iter):
    return [im.convert('L') for im in image_iter]
    # However, I doubt Pillow's RGBA->L Works well. 

def run(config_file_name):
    d = parse_config(config_file_name)
    for no in range(d["page_start"],d["page_end"]+1):
        if no in d["exempt"]:
            continue
        inputfile = d["input"] % no
        outputfile = d["output"] % no
        try:
            im = Image.open(inputfile)
        except FileNotFoundError:
            print("the file {%s} does not exist" % inputfile)
            continue
        image_iter = [roll(im,d["roll_up"],d["roll_down"],d["roll_left"],d["roll_right"])]
        if d["vertical_chunk"] == 2:
            image_iter = vertical_split(image_iter)
        if d["horizontal_chunk"] == 2:
            image_iter = horizontal_split(image_iter)
        for nnnn,im in enumerate(into_greyscale(image_iter)):
            temp = roll(im,d["roll_up_after"],d["roll_down_after"],d["roll_left_after"],d["roll_right_after"])
            temp = preprocess(temp,no,d["default_lines"],d["ratio"])
            if temp is not None and len(image_iter)>1:
                temp.save(outputfile.replace(".","_%d." % nnnn))
            elif temp is not None:
                temp.save(outputfile)

def parse_config(filename):
    ret = {}
    with open(filename,"r") as config:
        lines = config.readlines()
        for line in lines:
            line = line.strip()
            if len(line)==0 or line[0]=='#':
                continue
            space = line.find(" ")
            word = line[:space].strip()
            if word == "line_furigana_ratio":
                ret["ratio"] = eval(line[space+1:])
            elif word == "output":
                ret["output"] = line[space+1:].replace("{{}}",f"%0{ret['input_digits']}d").strip() 
            elif word == "input":
                ret["input"] = line[space+1:].replace("{{}}",f"%0{ret['input_digits']}d").strip()
            elif word == "exempt":
                ret["exempt"] = [int(no) for no in line.split(" ")[1:]]
            else:
                ret[word] = int(line[space+1:])
    print(ret)
    return ret

if __name__=="__main__":
    # try:
    run(sys.argv[1])
    #except IndexError:
        #print(f"format: python3 {sys.argv[0]} (config file name)")

