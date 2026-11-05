from pathlib import Path
import json,zipfile,hashlib
root=Path.cwd();out=root/'outputs/four-board-study';rows=[json.loads(x) for x in (out/'results.jsonl').read_text().splitlines()];formal=[r for r in rows if r['formal']];assert len(formal)==10 and sum(r['target'] for r in formal)==1000000
for r in formal:
 bitmap=(out/f"{r['name']}-received.bin").read_bytes();assert sum(x.bit_count() for x in bitmap)==r['boards']['A']['unique']==100000
 assert r['boards']['A']['missing']==0 and sum(r['round_hist_25us'])==r['boards']['A']['hist_rounds']
for b in json.loads((out/'backup-manifest.json').read_text()):
 for suffix,k in [('flash','flash_sha256'),('uicr','uicr_sha256')]:assert hashlib.sha256((out/f"{b['board']}-before-fourboard-{suffix}.bin").read_bytes()).hexdigest()==b[k]
manifest=json.loads((out/'experiment-manifest.json').read_text());manifest['post_test_configuration_record']='D-uicr-restoration.json';manifest['tested_D_uicr']='D-tested-uicr.bin';manifest['final_verification']='post-test-verification.json';(out/'experiment-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
with zipfile.ZipFile(out/'analysis-and-report-scripts.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ('analyze-four.py','plot-four.py','report-four.py','verify-four-final.py','verify-four-fault.py','postrestore-four.py'):
  z.write(root/'work'/name,name)
text='''四节点 UWB 实验交付说明
正式完成 10 组，每组 100000 条四字节应用数据，共 100 万条，最终全部收到。
逐个点名三个节点平均 6.039 ms；分时回复最佳扫描间隔 636 μs，平均 4.081 ms，耗时减少 32.4%。
两叶节点直接上报平均 4.385 ms；两跳逐包转发 9.014 ms；两跳聚合 8.374 ms，聚合耗时减少 7.1%。
逐包转发有 1/50000 轮超过 100 ms，最大 129.961 ms；聚合本次最大 68.837 ms。
按当前三节点小组串行复制估算，100 ms 可安排 72 个节点的数据，300 个节点约 408.4 ms。数百节点为时间预算推算。

正式数据见 results.jsonl 中 formal=true 的十组。其他行是短样本调试与恢复后检查。
树形首次到达率指首次收集请求期间的到达率，包含中继对下游的重试。
图表、源代码、固件和四板原始备份均已保存。四板当前程序与测试固件一致。
D 板复位引脚配置的差异及恢复记录见 D-uicr-restoration.json；当前配置已与原备份核对一致，恢复后两组短测试全部收齐。
下一步优先重复最佳间隔，测量接收处理耗时，扩大一次点名的节点数，并缩短两跳完成等待。
''';(out/'交付说明.txt').write_text(text,encoding='utf-8-sig')
report=root/'outputs/四节点UWB组网可行性实验报告.docx';bundle=root/'outputs/四节点UWB实验数据与代码.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as z:
 z.write(report,report.name)
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,str(p.relative_to(out)))
with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
print(json.dumps(dict(formal_cases=len(formal),records=1000000,missing=0,report_bytes=report.stat().st_size,bundle_bytes=bundle.stat().st_size,checks='bitmaps, counters, histograms, backups, archive CRC passed'),ensure_ascii=False))
