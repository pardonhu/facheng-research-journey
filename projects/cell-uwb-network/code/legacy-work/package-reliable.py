from pathlib import Path
import json,shutil,hashlib,zipfile,subprocess
root=Path.cwd(); out=root/'outputs'; results=out/'reliable-runs'
p=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Reliable'
rows=[json.loads(x) for x in (results/'results.jsonl').read_text().splitlines()]
lines=['UWB 分组确认与重传验证','',
'日期：2026-11-03',
'来源：toolnail/UWB，commit 79209d263fc536fbffd4c5af5b2e4c4b610eeedb，Src/examples/ex_08_reliable_p2p。',
'实现：新增 Build_Platforms/nRF52832-Reliable，复用 RP v1 帧格式、载荷校验与位图辅助函数，适配已验证的 nRF52832 SPI/计时平台。',
'机制：会话握手；每组32包；位图确认；每包最多首发1次+补发4次；会话结束后接收端回报去重收包数。控制握手/结束最多尝试10次。',
'ACK丢失时，沿用原发送算法，在下一轮补发尚未确认的包；接收端去重。末组不足32包时只确认有效位。',
'每次命令可设置1至100000包、间隔、方向、重传轮数和故障注入。两块板使用同一个固件。',
'硬件：PCA10040/nRF52832 + DWM3000EVB，A=JLINK_A，B=JLINK_B。',
'配置：信道5，6.8Mbps，前导码128，PAC8，STS关闭；发射功率寄存器0xfdfdfdfd。',
'数据和控制帧均59字节（含2字节FCS），其中数据帧有效载荷32字节。PAN=0xDECA，TX=0x5458，RX=0x5258。',
'此处32包是一组确认窗口，每包单独发送。',
'等待：数据发送结束后150us；控制响应前300us；收到确认后300us；ACK软件等待上限10000us。',
'全会话去重位图12500字节，最大100000包，适合64KB RAM。',
'', '统计定义：',
'first_unique：接收端首次尝试收到的唯一数据包数。recovered：首次收到该包时，其发送轮次已大于0。',
'retransmissions：发送端实际完成的补发次数，包含因ACK丢失造成的重复发送。',
'remote_failed：结束汇总中接收端报告的最终缺包数。ack_missing：发送端在每组结束时仍未获确认的包数。',
'state=3表示发送流程结束且收到了合法汇总；是否全部交付看remote_failed。',
'人为丢包在接收端通过载荷校验后执行，用于协议验证。injection=1丢弃序号为10倍数的首次尝试；=2丢弃这些包的所有尝试。',
'ack_drop=N：每N个窗口丢弃该窗口的第一次确认响应。',
'elapsed：发送端从握手前到最终汇总收到的板载计时，包含处理、SPI、等待、重传、控制交换。调试器读取期间的影响未单独扣除。',
'本轮用途：验证重传、去重、终止和统计；现场位置沿用当前摆位。',
'', '测试结果：']
for r in rows:
 t=r['tx'];s=r['rx'];n=r['count']
 lines.append(f"{r['name']}: N={n}, 首次={s['first_unique']}, 补发恢复={s['recovered']}, 最终={s['unique']}/{n}, 最终缺包={t['remote_failed']}, 补发次数={t['retransmissions']}, ACK超时={t['ack_timeouts']}, 接收重复={s['duplicates']}, 总耗时={t['elapsed']/1e6:.6f}s, 人为丢弃DATA次数={s['injected']}, 人为丢ACK={s['ack_dropped']}")
(out/'UWB重传验证结果.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
shutil.copy2(p/'build/uwb-reliable.hex',out/'uwb-reliable.hex')
manifest={'sha256':hashlib.sha256((out/'uwb-reliable.hex').read_bytes()).hexdigest(),'results':len(rows),'source_commit':subprocess.check_output(['git','-C',str(root/'work/toolnail-UWB'),'rev-parse','HEAD'],text=True).strip()}
(results/'manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(out/'UWB重传程序与验证.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['main.c','build.py','memory.ld']:z.write(p/name,'nRF52832-Reliable/'+name)
 z.write(root/'work/test-reliable.py','test-reliable.py')
 for f in (p.parents[1]/'Src/examples/ex_08_reliable_p2p').glob('*.[ch]'):z.write(f,'original-colleague/'+f.name)
 z.write(out/'UWB重传验证结果.txt','验证结果.txt');z.write(out/'uwb-reliable.hex','uwb-reliable.hex')
 for name in ['results.jsonl','manifest.json','flash-JLINK_A.log','flash-JLINK_B.log']:z.write(results/name,'evidence/'+name)
print('\n'.join(lines[-len(rows):]))
