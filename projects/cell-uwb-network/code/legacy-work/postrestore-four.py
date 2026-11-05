from four_io import *
try:
 run_case('post-restore-group',1,3000,formal=False)
 run_case('post-restore-aggregate',3,2000,mask=6,formal=False)
 (out/'status.json').write_text(json.dumps(dict(state='complete',formal_cases=10,post_restore_smoke_complete=True,completed=time.time())))
finally:
 for b in boards:stop(b)
