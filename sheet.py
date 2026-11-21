import sys,glob
from PIL import Image
files=sys.argv[2:];out=sys.argv[1]
ims=[Image.open(f).resize((360,640)) for f in files]
cols=min(4,len(ims));rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(cols*360,rows*640),'black')
for i,im in enumerate(ims):S.paste(im,((i%cols)*360,(i//cols)*640))
S.save(out)
