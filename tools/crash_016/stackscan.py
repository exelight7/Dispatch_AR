import sys,struct,runpy
sys.argv=[sys.argv[0],sys.argv[1]]
g=runpy.run_path('dump_read.py',run_name='x') if False else None
