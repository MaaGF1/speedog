# MaaFramework Speedog

一个为 MaaFramework 设计的基于日志的动态变速系统。

Speedog 通过实时分析 MaaFramework 的日志文件来感知当前的任务进度。它利用简单的节点映射规则，根据当前执行的任务节点自动调整游戏进程的速度(基于 `xspeedhack`)，从而实现"战斗时加速，交互时还原"的智能化控制。

## 一、功能特性

* 非侵入式监控: 通过 `debug/maa.log` 文件监控代理，无需注入 MaaFramework 内部。
* 动态变速: 根据日志中出现的特定节点(Node)，实时调整游戏进程的运行速度。
* 自动连接: 自动查找并连接到目标游戏进程，支持断线重连。
* 简单配置: 摒弃复杂的状态机，仅需配置 `节点 -> 速度倍率` 的简单映射。
* 安全保护: 程序退出时自动重置游戏速度为 1.0x，避免影响后续正常游戏。

## 二、使用源码

Python 版本要求 3.8 及以上。

1.  克隆仓库: 

```bash
git clone git@github.com:MaaGF1/speedog.git
# 或者
git clone https://github.com/MaaGF1/speedog.git
# 进入目录
cd speedog
```

2.  安装依赖: 

主要依赖用于 `xspeedhack` 库: 

```bash
pip install xspeedhack
```

## 三、配置说明

系统完全通过 `speedog.conf` 文件进行控制。

### 3.1 游戏设置

配置目标游戏进程的信息，以便 Speedog 进行连接和变速。

```ini
[Game]
# 目标游戏进程名称
Process_Name=GrilsFrontLine.exe

# 进程架构，通常为 x64 或 x86
Process_Arch=x64
```

### 3.2 监控设置

将 Speedog 指向你的 MaaFramework 日志文件。

```ini
[Monitoring]
# MaaFramework 生成的日志文件路径
Log_File_Path=../debug/maa.log

# 轮询间隔(秒)
Monitor_Interval=1.0
```

### 3.3 变速规则

#### 节点规则 (`[Nodes]`)
格式: `规则名称={触发节点名, 目标速度倍率}`

*   NodeName (触发节点名): 日志中出现的、MaaFramework Pipeline 中的节点名称。
*   SpeedMultiplier (目标速度倍率): 当检测到该节点时，应用的速度倍数(浮点数)。

```ini
[Nodes]
# 示例: 当检测到 'Combat_Start' 节点时，将速度设置为 5.0 倍
Combat_Boost={Combat_Start, 5.0}

# 示例: 当检测到 'Menu_Entry' 节点时，将速度重置为 1.0 倍
Menu_Reset={Menu_Entry, 1.0}

# 实际需求示例: 
# 当检测到 'ad逃亡_结束回合1' 时，开启 10 倍速
BLM_Loop={ad逃亡_结束回合1, 10.0}
```

## 四、使用方法

### 4.1 启动 Speedog

运行主脚本。它将阻塞并无限期地监控日志文件。

```bash
python main.py
```

### 4.2 命令行参数

* `--config <path>`: 指定自定义配置文件路径。

示例:

```bash
python main.py --config ./my_configs/speedog.conf
```

## 五、How it works

1. 初始化: Speedog 读取配置文件，并尝试通过 `Process_Name` 连接到游戏进程。
2. 日志解析: `LogMonitor` 读取 `maa.log` 中的新行。它寻找类似 `[pipeline_data.name=NodeName] | enter` 的模式。
3. 规则匹配: 当检测到一个新节点时，系统会在 `[Nodes]` 配置中查找是否存在对应的规则。
4. 执行变速: 
    * 如果找到匹配规则(例如 `NodeA -> 10x`)，`GameSpeedController` 会立即调用 `xspeedhack` 接口修改游戏内存速度。
    * 如果未找到规则，保持当前速度不变。
5. 退出清理: 当用户停止程序(Ctrl+C)时，Speedog 会自动将游戏速度重置为正常值(1.0x)。