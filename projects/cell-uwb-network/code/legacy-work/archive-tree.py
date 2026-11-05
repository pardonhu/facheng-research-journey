from pathlib import Path
import zipfile,json,hashlib
root=Path.cwd();out=root/'outputs/tree-end-to-end-study';base=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms'
assert (out/'post-test-verification.json').exists()
info=dict(repository='https://github.com/toolnail/UWB',base_commit='79209d263fc536fbffd4c5af5b2e4c4b610eeedb',compiler='arm-none-eabi-gcc 14.2.1',jlink='V9.90',formal_cases=6,original_leaf_records_per_case=50000,records_per_round=2,topology='C/D -> B -> A; direct control C/D -> A',channel=5,data_rate='6.8 Mbps',record_bytes=4,artificial_loss=False,simulation='none; 200/300 record windows are consecutive measured groups on the same physical topology',firmware_sha256={chip:hashlib.sha256((base/f'nRF{chip}-Tree/build/uwb-tree.hex').read_bytes()).hexdigest() for chip in ('52832','52840')})
(out/'experiment-manifest.json').write_text(json.dumps(info,indent=2))
readme='''# 四板全过程实验数据说明

先阅读 outputs 中的《四板电芯到中继再到中心全过程实验.md》。

- results.jsonl 包含短测试和正式测试，以 formal 字段区分；仅6组 formal=true 进入正式对照。
- 每组正式测试50000条叶节点原始记录，C、D各25000条；补发另计。聚合包包含两条。
- windows.200/300 保存连续采集100/150组的实际耗时和缺失记录数。该时间用于等效200/300电芯串行采集推算，实体叶节点始终为两个。
- phase.B.collection_us 累加中继点名叶节点并等待数据的本地耗时。
- phase.B.uplink_us 累加中继准备、等待200us并发送数据的本地耗时。
- round_hist_25us 每格25us，最后一格为>=102375us；200/300记录时间窗口保留完整微秒数。
- received.bin 按原始记录序号存位图，低位在前；每轮C在前、D在后。
- turn_us 为点名RX时间标记到回复TX时间标记的计划延迟，不是空口帧尾到帧头IFS。
- filtered 为硬件地址过滤事件；叶节点的 invalid 还包含收到不属于其父节点的根节点广播确认，不能直接当作损坏数据包数。
- 此前的500us短测试全部失败，保留原始记录；本次正式 fast 配置使用通过检查的750us。
- C/D生成四字节测试值，没有连接电芯传感器；没有包含传感器采样时间。
- 报告中每组全程包括中心请求、叶节点采集、中继转发、结束通知、确认和等待。
- before-flash.bin 与 before-uicr.bin 保存四板本轮前状态；before-source.zip 保存原程序。

source 提供独立 nRF52832-Tree 与 nRF52840-Tree 工程、固件、主机脚本。
工程使用同学仓库的SDK与驱动。prepare-tree.py 基于保留的Four工程生成Tree工程；完整生成后的main.c已随包提供。
主机脚本会操作真实设备，板卡序列号和J-Link路径见tree_io.py。
构建脚本查找当前工作区 work/arm-gcc；恢复到原仓库对应 Build_Platforms 位置后可重新编译。
'''
(out/'数据说明.md').write_text(readme,encoding='utf-8')
dest=root/'outputs/四板全过程实验数据与代码.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
 for f in out.rglob('*'):
  if f.is_file():z.write(f,out.name+'/'+f.relative_to(out).as_posix())
 for chip in ('52832','52840'):
  project=base/f'nRF{chip}-Tree'
  for f in project.rglob('*'):
   if f.is_file() and f.suffix!='.o':z.write(f,'source/'+project.name+'/'+f.relative_to(project).as_posix())
 for name in ('prepare-tree.py','prepare-tree-host.py','tree-body.c','tree_io.py','run-tree.py','scan-tree.py','analyze-tree.py','air-budget-tree.py','report-tree.py','verify-tree.py','archive-tree.py','backup-tree.py','tree-smoke.log','tree-scan.log','tree-formal.log','build-tree32.log','build-tree40.log'):
  z.write(root/'work'/name,'source/'+name)
 z.write(root/'outputs/四板电芯到中继再到中心全过程实验.md','四板电芯到中继再到中心全过程实验.md')
assert zipfile.ZipFile(dest).testzip() is None
print(dest)
