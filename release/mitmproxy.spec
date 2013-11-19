# -*- mode: python -*-
# PyInstaller Spec File

from PyInstaller.build import *

scripts = ['mitmdump', 'mitmproxy-gui']
if not os.name == "nt":
    scripts.append('mitmproxy')

analyses = list(Analysis(scripts=['../dist/%s' % s]) for s in scripts)

# If we use MERGE, our binaries break
# Alternatively, we could exclude binaries and save them in the folder,
# but that looks ugly and makes them less portable. 6MB is reasonable.
#merge_info = []
#for i, a in enumerate(analyses):
#    merge_info.append((a, scripts[i], scripts[i] + '.exe'))
#MERGE(*merge_info)

gui_tree = Tree('../dist/libmproxy/gui', prefix='libmproxy/gui')
scripts_tree = Tree('../dist/scripts', prefix='scripts')

executables = []
for i, a in enumerate(analyses):
    pyz = PYZ(a.pure)
    executables += [
        # a.binaries,
        EXE(pyz,
            a.scripts,
            a.binaries,
            # exclude_binaries=True,
            name=scripts[i] + '.exe',
            console=True)]
COLLECT(gui_tree,
        scripts_tree,
        *executables,
        name="dist")
