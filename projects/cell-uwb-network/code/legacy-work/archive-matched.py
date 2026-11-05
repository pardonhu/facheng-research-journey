from pathlib import Path
import hashlib,json,zipfile
root=Path.cwd();out=root/'outputs/ble-matched-study'
assert json.loads((out/'status.json').read_text())['state']=='complete'
assert (out/'post-test-verification.json').exists()
project=root/'work/toolnail-UWB/DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52832-Matched'
info=dict(repository='https://github.com/toolnail/UWB',base_commit='79209d263fc536fbffd4c5af5b2e4c4b610eeedb',project=str(project),compiler='arm-none-eabi-gcc 14.2.1',jlink='V9.90',formal_cases=15,original_data_packets_per_case=50000,requested_ifs_us=150,preambles=[128,64,32],boards=dict(A='JLINK_A',B='JLINK_B'),C_D='not flashed in this experiment',usb_recovery='p64-m0-a1 completed on hardware; transient J-Link read failure; preserved RAM counters and bitmap recovered, case not rerun',firmware_sha256=hashlib.sha256((project/'build/uwb-matched.hex').read_bytes()).hexdigest())
(out/'experiment-manifest.json').write_text(json.dumps(info,indent=2))
if (out/'error.txt').exists():(out/'error.txt').rename(out/'recovered-JLink-read-error.txt')
readme='''UWB 蓝牙同规则容量实验数据包

阅读顺序：
1. 实时容量结果.txt：15 组硬件结果及容量估算。
2. hardware-summary.json：实测平均、P95、P99、收齐率、实际间隔。
3. model-results.json 与 model-capacity.json：同学规则下的模拟和理论容量。
4. results.jsonl：全部原始计数、每300条周期及发包周期直方图；formal=false 为短测试。
5. 每组 received.bin：按原始 DATA 序号的接收位图，低位对应较小序号。
原始字段 timeouts 统计失败尝试，含人为丢弃DATA后重试，不等于实际等满1000us的次数。

每组 50000 指不同序号的原始 DATA 包。固定五次有 250000 次发射；POLL 补发另计。
聚合包含10条30bit数据，因此每组聚合含500000条应用记录。
128 为历史前导码，64 为此前四板配置，32 为128的四分之一。
POLL 的10%人工丢包分别施加在POLL和DATA；自然丢包另计。
单次发送使用自然链路，不注入丢包。所有帧均进行序号和内容校验。

模型中每次尝试为POLL+150us+DATA+150us，末尾减150us。
硬件包含主控处理、实际帧间隔和1000us回复超时，区别已写入报告。
10条聚合默认数据已经在发送端准备好；尚未包含10个不同物理节点的收集时间。
100ms容量是逻辑记录的时间预算推算，当前链路实测使用A/B两板。
物理摆放保持本次现场状态，未测量距离、朝向与遮挡，不与其他场地成功率直接比较。

source 中包含新工程完整main.c、构建脚本、固件及主机脚本。
重编译可将工程放回清单中同学仓库的 Build_Platforms 目录，使用仓库自带SDK/驱动及本地GCC。
运行主机脚本会直接操作开发板；参数、序列号和J-Link路径写在 run-matched.py 中。
模型脚本需NumPy；文档脚本需python-docx。软件版本和SHA256见experiment-manifest.json。
before-flash.bin 和 before-uicr.bin 是本轮烧录前的备份；before-source.zip 是此前四板程序。
post-test-verification.json 记录测试后固件和UICR核对结果。
recovered-JLink-read-error.txt 为已恢复的一次读取错误，实验最终状态见status.json。
'''
(out/'数据说明.txt').write_text(readme,encoding='utf-8-sig')
dest=root/'outputs/UWB前导码容量实验数据与代码.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
    for f in out.rglob('*'):
        if f.is_file():z.write(f,'data/'+f.relative_to(out).as_posix())
    for f in project.rglob('*'):
        if f.is_file() and f.suffix!='.o':z.write(f,'source/nRF52832-Matched/'+f.relative_to(project).as_posix())
    for name in ('matched-body.c','prepare-matched.py','run-matched.py','model-matched.py','capacity-matched.py','analyze-matched.py','verify-matched.py','report-matched.py','plot-matched.py','archive-matched.py','matched-formal.log','matched-resume.log','build-matched.log'):
        f=root/'work'/name
        if f.exists():z.write(f,'source/'+name)
print(dest)
