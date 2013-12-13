# -*- mode: python -*-
# PyInstaller Spec File

from PyInstaller.build import *
import os, sys, shutil
from os.path import join

EXT = ".exe" if (os.name == "nt") else ""
src_dir = "../dist/source"
dst_dir = join("../dist/", sys.platform)

if os.path.isdir(dst_dir):
    print "Delete old release..."
    shutil.rmtree(dst_dir)

scripts = ['mitmdump', 'mitmproxy-gui']
if os.name != "nt":
    scripts.append('mitmproxy')

analyses = []
for s in scripts:
    a = Analysis(scripts=[join(src_dir, s)])
    analyses.append(a)
    # http://www.pyinstaller.org/ticket/783
    for d in a.datas:
        if 'pyconfig' in d[0]: 
            a.datas.remove(d)
            break

merge_info = []
for i, a in enumerate(analyses):
    merge_info.append((a, scripts[i], scripts[i] + EXT))
MERGE(*merge_info)

for i, a in enumerate(analyses):
    pyz = PYZ(a.pure)
    EXE(pyz,
        a.scripts,
        a.binaries,
        a.datas,
        a.zipfiles,
        a.dependencies,
        name=scripts[i] + EXT,
        console=True)

print "Pack release..."
os.renames("./dist", dst_dir)
os.mkdir(join(dst_dir, "libmproxy"))
print "."
shutil.copytree(join(src_dir,"libmproxy/gui"), join(dst_dir, "libmproxy/gui"))
print "."
shutil.copytree(join(src_dir, "scripts"), join(dst_dir, "scripts"))
print "."
for fname in os.listdir(src_dir):
    f = join(src_dir, fname)
    if os.path.isfile(f) and fname not in ['mitmdump', 'mitmproxy', 'mitmproxy-gui']:
        shutil.copy(f, join(dst_dir, fname))

print "Done!"