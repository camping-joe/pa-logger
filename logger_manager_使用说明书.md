# pa日志管理模块使用说明书

版本：1.0.0

发布时间：2026.03.09

## 1. 模块简介

`logger_manager.py` 是一个基于 Python 标准库 `logging` 的日志管理模块，提供统一的日志器创建、文件轮转、多格式输出等功能。通过名称缓存机制，同一名称的日志器只会创建一次，便于在多模块中复用。

**主要特性：**

- 支持按大小或按时间轮转日志文件
- 支持控制台与文件双通道输出
- 四种输出格式可选（标准 / 纯内容 / 时间+内容 / 用户自定义）
- 五种日志级别（debug / info / warning / error / critical）
- 日志器按名称单例，避免重复创建

---

## 2. 依赖与环境

- **Python 版本**：需支持 `logging`、`enum`（通常 Python 3.x 均可）
- **标准库**：`logging`、`logging.handlers`、`enum`

无需安装第三方依赖，将 `logger_manager.py` 放在项目路径下即可导入使用。

---

## 3. 核心类型说明

### 3.1 文件轮转方式 `FileRotatingType`

| 枚举值 | 说明 |
|--------|------|
| `bytesRotating` | 按文件大小轮转（默认），超过阈值后新建文件并保留备份 |
| `timedRotating` | 按时间周期轮转（如按天），到期后新建文件并保留备份 |
| `noneIndependentFileLog` | 预留，当前实现中未单独处理 |

### 3.2 输出级别 `OutType`

| 枚举值 | 说明 |
|--------|------|
| `OutType.debug` | 调试级别 |
| `OutType.info` | 信息级别（默认） |
| `OutType.warning` | 警告级别 |
| `OutType.error` | 错误级别 |
| `OutType.critical` | 严重错误级别 |

### 3.3 输出格式 `Out_formatter_type`

| 枚举值 | 说明 |
|--------|------|
| `custom_formatter` | 标准格式：`[时间 级别 日志器名] 消息内容` |
| `plain_formatter` | 纯内容：仅输出消息内容 |
| `time_formatter` | 时间+内容：`[时间] 消息内容` |
| `user_defined_formatter` | 用户自定义格式，需同时传入参数 `user_defined_formatter_str` |

前三种格式实际使用的格式对象来自模块全局变量（`Custom_formatter`、`Plain_formatter`、`Time_formatter`），因此可在运行时通过 `set_custom_formatter` / `set_time_formatter` 修改，对之后所有使用该格式的 `writelog` 调用都会生效（包括已创建的日志器）。`user_defined_formatter` 在每次调用时由 `user_defined_formatter_str` 指定，可同时自定义整体格式与时间格式（用逗号分隔）。

---

## 4. 主要 API

### 4.1 获取日志器：`get_logger(...)`

根据名称获取或创建日志器。若该名称的日志器已存在，则直接返回缓存实例；否则按参数创建并缓存。

**函数签名：**

```python
def get_logger(
    logger_name: str,
    file_name: str,
    file_max_size: int = 5,
    file_backup_count: int = 5,
    file_rotating_interval: int = 7,
    level: int = logging.DEBUG,
    file_rotating_type: FileRotatingType = FileRotatingType.bytesRotating,
)
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `logger_name` | str | 必填 | 日志器名称，不能为 `None` 或空/纯空白字符串 |
| `file_name` | str | 必填 | 日志输出文件路径（含文件名） |
| `file_max_size` | int | 5 | 按大小轮转时的单文件最大体积（MB） |
| `file_backup_count` | int | 5 | 保留的备份文件数量 |
| `file_rotating_interval` | int | 7 | 按时间轮转时的周期数（如 7 表示每 7 天） |
| `level` | int | `logging.DEBUG` | 日志器级别，如 `logging.INFO`、`logging.ERROR` |
| `file_rotating_type` | FileRotatingType | `bytesRotating` | 轮转方式 |

**返回值：** `LoggerManager` 实例。

**异常：** 若 `logger_name` 为 `None`、空字符串或非字符串，会抛出 `TypeError`。

---

### 4.2 写入日志：`LoggerManager.writelog(...)`

向当前日志器写入一条日志，可同时输出到控制台和文件，并可指定格式、级别与是否立即刷盘。

**方法签名：**

```python
def writelog(
    self,
    content: str,
    out_formatter_type: Out_formatter_type = Out_formatter_type.custom_formatter,
    out_type: OutType = OutType.info,
    flush: bool = False,
    user_defined_formatter_str: str = None,
)
```

**参数说明：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `content` | str | 必填 | 要输出的日志内容 |
| `out_formatter_type` | Out_formatter_type | `custom_formatter` | 本条日志使用的输出格式 |
| `out_type` | OutType | `OutType.info` | 日志级别（debug/info/warning/error/critical） |
| `flush` | bool | False | 是否立即将文件缓冲写入磁盘（指写入硬盘，非控制台） |
| `user_defined_formatter_str` | str | None | 仅当 `out_formatter_type=user_defined_formatter` 时必填。整体格式与时间格式用逗号 `,` 分隔；不写逗号则仅传整体格式，时间使用系统默认 |

**异常：** 当 `out_formatter_type` 为 `user_defined_formatter` 且未传或传入 `None` 的 `user_defined_formatter_str` 时，抛出 `ValueError`。

---

### 4.3 类方法：自定义格式

#### `LoggerManager.set_custom_formatter(fmt, datefmt)`

修改“标准格式”的模板和时间格式。调用后会更新全局 `Custom_formatter`，**会立即生效**：之后任意日志器（含已创建的实例）在 `writelog(..., out_formatter_type=custom_formatter)` 时都会使用新格式。

| 参数 | 说明 |
|------|------|
| `fmt` | 格式字符串，如 `"%(asctime)s %(levelname)s %(message)s"` |
| `datefmt` | 时间格式，如 `"%Y-%m-%d %H:%M:%S"` |

#### `LoggerManager.set_time_formatter(datefmt)`

修改“时间+内容”格式中的时间显示格式。调用后会更新全局 `Time_formatter`，**会立即生效**：之后任意日志器在选用 `time_formatter` 时都会使用新时间格式。

| 参数 | 说明 |
|------|------|
| `datefmt` | 时间格式字符串 |

---

## 5. 使用示例

### 5.1 基础用法（按大小轮转）

```python
import logging
from logger_manager import get_logger, OutType, Out_formatter_type

# 获取名为 "my_app" 的日志器，日志写入 logs/app.log，单文件最大 10MB，保留 3 个备份
logger = get_logger(
    logger_name="my_app",
    file_name="logs/app.log",
    file_max_size=10,
    file_backup_count=3,
    level=logging.INFO,
)

# 写入不同级别的日志
logger.writelog("程序启动", out_type=OutType.info)
logger.writelog("调试信息", out_type=OutType.debug)
logger.writelog("发生错误", out_type=OutType.error, flush=True)  # 立即写入文件
```

### 5.2 按时间轮转

```python
from logger_manager import get_logger, FileRotatingType
import logging

logger = get_logger(
    logger_name="daily_log",
    file_name="logs/daily.log",
    file_rotating_type=FileRotatingType.timedRotating,
    file_rotating_interval=1,   # 每 1 天轮转
    file_backup_count=7,
    level=logging.INFO,
)
logger.writelog("按天轮转的日志示例")
```

### 5.3 使用不同输出格式

```python
from logger_manager import get_logger, Out_formatter_type, OutType

logger = get_logger("formatter_demo", "logs/demo.log")

# 标准格式（时间+级别+名称+内容）
logger.writelog("这是标准格式", out_formatter_type=Out_formatter_type.custom_formatter)

# 仅内容
logger.writelog("仅内容", out_formatter_type=Out_formatter_type.plain_formatter)

# 时间 + 内容
logger.writelog("时间+内容", out_formatter_type=Out_formatter_type.time_formatter)
```

### 5.4 用户自定义格式

```python
from logger_manager import get_logger, Out_formatter_type

logger = get_logger("demo", "logs/demo.log")

# 仅自定义整体格式，时间用系统默认
logger.writelog(
    "仅整体格式",
    out_formatter_type=Out_formatter_type.user_defined_formatter,
    user_defined_formatter_str="%(levelname)s | %(message)s",
)

# 整体格式与时间格式用逗号分隔：前面是 fmt，后面是 datefmt
logger.writelog(
    "自定义格式+时间",
    out_formatter_type=Out_formatter_type.user_defined_formatter,
    user_defined_formatter_str="[%(asctime)s] %(name)s - %(message)s,%Y-%m-%d %H:%M:%S",
)
```

### 5.5 多模块共用同一日志器

```python
# 模块 A
from logger_manager import get_logger
logger = get_logger("shared", "logs/shared.log")
logger.writelog("来自模块 A")

# 模块 B（同一进程内）
from logger_manager import get_logger
logger = get_logger("shared", "logs/shared.log")  # 返回已存在的 "shared" 日志器
logger.writelog("来自模块 B")
```

### 5.6 全局修改标准格式与时间格式

```python
from logger_manager import LoggerManager

LoggerManager.set_custom_formatter(
    fmt="[%(asctime)s] %(name)s - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
LoggerManager.set_time_formatter(datefmt="%H:%M:%S")
```

---

## 6. 类属性说明（LoggerManager）

| 属性 | 说明 |
|------|------|
| `instance_dict` | 类字典，缓存所有已创建的日志器实例（key 为 `logger_name`） |
| `file_handlers_dict` | 类字典，按 `file_name` 缓存文件处理器，同文件路径复用同一 handler |
| `global_log_file_path` | 预留：总日志文件绝对路径，当前未在逻辑中使用 |

---

## 7. 注意事项

1. **`logger_name`**：必须为非空字符串且不能仅为空白字符，否则会抛出 `TypeError`。
2. **文件路径**：`file_name` 建议使用绝对路径或相对项目根目录的路径；若目录不存在，需自行先创建，否则写文件可能失败。
3. **轮转类型**：当前实现中，`FileRotatingType.noneIndependentFileLog` 未单独分支，实际创建文件 handler 时仅处理了 `bytesRotating` 和 `timedRotating`。
4. **编码**：文件 handler 固定使用 `utf-8` 编码。
5. **传播**：日志器的 `propagate` 已设为 `False`，不会向根 logger 传递，避免重复输出。
6. **格式作用域**：`writelog` 每次调用会设置当前 stream 与 file 的 formatter，因此不同调用可使用不同格式；`set_custom_formatter` / `set_time_formatter` 修改的是全局的格式对象，会影响之后所有使用该格式类型的日志。选用 `user_defined_formatter` 时必须传入有效的 `user_defined_formatter_str`，否则会抛出 `ValueError`。

---

## 8. 快速参考

| 需求 | 建议 |
|------|------|
| 获取日志器 | `get_logger(logger_name, file_name, ...)` |
| 写一条日志 | `logger.writelog(content, out_type=OutType.info)` |
| 立即落盘 | `logger.writelog(..., flush=True)` |
| 按大小轮转 | `file_rotating_type=FileRotatingType.bytesRotating`，设 `file_max_size` |
| 按天轮转 | `file_rotating_type=FileRotatingType.timedRotating`，设 `file_rotating_interval` |
| 改标准格式 | `LoggerManager.set_custom_formatter(fmt, datefmt)` |
| 改时间格式 | `LoggerManager.set_time_formatter(datefmt)` |
| 用户自定义格式 | `writelog(..., out_formatter_type=Out_formatter_type.user_defined_formatter, user_defined_formatter_str="fmt,datefmt")`，逗号可省略则仅传 fmt |

---

*文档对应模块：`logger_manager.py`*

