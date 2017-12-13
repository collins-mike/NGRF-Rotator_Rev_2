from distutils.core import setup
import matplotlib
import py2exe
 
#setup(zipfile="pyfiles/bar.zip",windows=['main.py'],options={"py2exe": {"skip_archive": True}})
setup(zipfile="pyfiles/shared.zip",windows=[{"script":"main.py"}], options={"py2exe":{"includes":["sip"]}}, data_files=matplotlib.get_py2exe_datafiles())