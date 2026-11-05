from pathlib import Path
p=Path('work/verify-four-final.py');s=p.read_text().replace('uicr_unchanged=same','uicr_matches_backup=same,reset_pin_configuration_restored_after_test=(b["label"]=="D")');p.write_text(s)
p=Path('work/report-four.py');s=p.read_text(encoding='utf8');needle="p('本次实验为组网协议可行性验证";a=s.index(needle);s=s[:a]+"p('收尾检查发现 D 板的两个 PSELRESET 字段为 0xFFFFFFFF，实验前备份为 0x00000012。已保留测试结束时的配置文件，并按备份恢复这两个字段。四板程序均与归档固件逐字节一致，当前板卡配置均与实验前备份一致；恢复后另做分时回复与两跳聚合短测试。该差异和恢复记录保存在 D-uicr-restoration.json。')\n"+s[a:];p.write_text(s,encoding='utf8')
