# 代码、固件与复现

**当前版本是MinGap，历史版本保留以核对证据。** 新模型先读项目STATE，不直接执行全部legacy脚本。

## 1 目录

- `firmware/platforms/nRF52832-MinGap/`和`nRF52840-MinGap/`：本次编译过的完整main.c、链接脚本、原构建脚本和固件。
- `legacy-work/min-gap-body.c`、`prepare-min-gap.py`：生成上述平台应用的原始入口。
- `legacy-work/run-min-gap.py`及三个后续扫描脚本：原工作区执行记录，对路径有依赖，公开版调试器序列号已改为标签。
- `tools/build_firmware.py`：迁移后独立构建入口，只编译。
- `tools/run_min_gap.py`：迁移后单组测试入口，显式选择烧录或使用已装固件。
- `tools/verify_records.py`：无需硬件的数据、位图、批次时间与固件哈希核对。

## 2 获取上游依赖

固定快照：[toolnail/UWB@79209d263fc536fbffd4c5af5b2e4c4b610eeedb](https://github.com/toolnail/UWB/tree/79209d263fc536fbffd4c5af5b2e4c4b610eeedb)。构建使用：

```text
DW3_QM33_SDK_1.1.1/Drivers/API/Shared/dwt_uwb_driver/
DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52840-DK/sdk/
DW3_QM33_SDK_1.1.1/Drivers/API/Build_Platforms/nRF52840-DK/SEGGER/
```

完整上游较大，可用Git稀疏检出上述目录。Nordic SDK为上游内置17.0.2；工具链使用Arm GNU Toolchain 14.2.Rel1。上游代码及SDK遵循各自许可，本项目未重新指定其许可；本目录不整体再分发SDK与工具链。

## 3 仅验证历史数据

在本项目目录运行：

```text
python code/tools/verify_records.py
```

它只读公开记录和接收位图，不连接调试器。

## 4 构建

```text
python code/tools/build_firmware.py --vendor <toolnail-UWB目录> --toolchain <arm-gcc的bin目录> --chip 52832
python code/tools/build_firmware.py --vendor <toolnail-UWB目录> --toolchain <arm-gcc的bin目录> --chip 52840
```

默认输出到对应平台的build目录；另可用`--output`放到独立目录，保留原始发布固件。原HEX/ELF对应实验中的固件SHA256。重新编译可能因路径、工具链及依赖差异改变哈希，新实验另记版本。

## 5 运行一组硬件实验

复制`device-config.example.json`为项目根目录的`device-config.local.json`，填入J-Link可执行文件、工具链bin目录及四个调试器序列号。该本机配置被gitignore排除。

```text
python code/tools/run_min_gap.py --config device-config.local.json --flash --preamble 64 --gap-us 30 --count 10000 --batch 300
```

`--flash`会先保存四板Flash/UICR再加载测试固件。匹配固件已装载时可改用`--use-installed`。运行结果在被gitignore排除的`runs/`。测试结束会停止四板收发。先确认当前任务授权和设备占用情况；本次归档没有运行该硬件入口。

## 6 验证范围

原始MinGap源码和固件已经完成四板实验；本次迁移的CLI层完成语法检查、帮助入口和离线数据验证，并用本机SDK与工具链构建两个目标。迁移后的运行CLI没有再次烧录或开展新实验。
