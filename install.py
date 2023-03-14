import sys
import os

file_path = 'src/autopcm.py'
exepath = "#!" + sys.executable + "\n"

with open(file_path, 'r') as f:
    old_content = f.read()
    firstline = old_content[:old_content.find('\n')]

if exepath != firstline:
    if firstline[0:2] == '#!':
        old_content = old_content[old_content.find('\n') + 1:]
    with open(file_path, 'w') as f:
        f.write(exepath + old_content)

home_dir = os.environ.get('HOME')
pwd_dir = os.environ.get('PWD')

if os.path.exists(home_dir + "/bin/autopcm"):
    os.remove(home_dir + "/bin/autopcm")
os.symlink(pwd_dir + "/src/autopcm.py", home_dir + "/bin/autopcm")


