import logging
from logging import handlers
from logging.handlers import (
    RotatingFileHandler,
    TimedRotatingFileHandler,
    BaseRotatingHandler,
)
from enum import Enum


# 两种日志轮转方式
class FileRotatingType(Enum):
    bytesRotating = 0
    timedRotating = 1
    noneIndependentFileLog = 2


# 5种输出级别类型
class OutType(Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


Custom_formatter = logging.Formatter(
    fmt="[%(asctime)s %(levelname)s %(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
Plain_formatter = logging.Formatter(fmt="%(message)s")
Time_formatter = logging.Formatter(
    fmt="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)


# 3种处理器输出格式


class Out_formatter_type(Enum):
    """
    custom_formatter:标准输出格式（时间+日志器名+Level）+具体内容
    plain_formatter:空白输出格式，只呈现日志内容
    time_formatter:时间+具体内容
    """

    custom_formatter = 0
    plain_formatter = 1
    time_formatter = 2
    user_defined_formatter = 3


def get_logger(
    logger_name: str,
    file_name: str,
    file_max_size: int = 5,
    file_backup_count: int = 5,
    file_rotating_interval: int = 7,
    level: int = logging.DEBUG,
    file_rotating_type: FileRotatingType = FileRotatingType.bytesRotating,
):
    """
    返回一个LoggerManager实例--日志器。根据名字判断是否已经创建过此日志器，如果创建过直接返回缓存中的，否则重新创建！
    Args:
        logger_name:日志器名称
        file_name:输出文件名称路径
        file_max_size:日志按大小分割的大小阈值,单位mb,默认5mb
        file_backup_count:日志的最大备份数量
        file_rotating_interval:日志按时间周期分割，最大轮转周期数
        level:日志器产生的日志级别
        file_rotating_type:日志文件轮转类型
    Returns:
        LoggerManager实例
    """
    if logger_name is None:
        raise TypeError("参数'logger_name'不能为 None，必须传入非空字符串！")
    if not logger_name.strip():
        raise TypeError("参数'logger_name'不能为空字符串，或者仅包含空白字符！")
    if not isinstance(logger_name, str):
        raise TypeError("参数'logger_name'必须传入字符串类型！")
    # 如果日志器缓存字典中有同名日志器，直接返回缓存中的日志器
    if logger_name in LoggerManager.instance_dict.keys():
        return LoggerManager.instance_dict[logger_name]

    if file_name in LoggerManager.file_handlers_dict.keys():
        file_handler = LoggerManager.file_handlers_dict.get(file_name)
    else:
        if file_rotating_type == FileRotatingType.bytesRotating:
            # 大小轮转默认1MB更新一次日志文件，默认备份5个最新日志文件
            file_handler = RotatingFileHandler(
                filename=file_name,
                maxBytes=file_max_size * 1024 * 1024,
                backupCount=file_backup_count,
                encoding="utf-8",
            )
        elif file_rotating_type == FileRotatingType.timedRotating:
            # 时间轮转日志默认7天更新一次,默认备份5个最新日志文件
            file_handler = TimedRotatingFileHandler(
                filename=file_name,
                when="D",
                interval=file_rotating_interval,
                backupCount=file_backup_count,
                encoding="utf-8",
            )
        LoggerManager.file_handlers_dict[file_name] = file_handler

    logger = LoggerManager(
        logger_name=logger_name, level=level, file_handler=file_handler
    )
    return logger


class LoggerManager:
    # 类字典，用来动态记录记录新建和销毁的日志器实例
    instance_dict = {}
    # 处理器字典
    file_handlers_dict = {}
    # 【功能预留】如果项目有一个总的日志文件，可以设置到这个类属性中，必须写绝对路径
    global_log_file_path = ""

    def __init__(self, logger_name: str, level: int, file_handler: BaseRotatingHandler):
        # 控制台处理器
        self.file_handler = file_handler
        self.stream_handler = logging.StreamHandler()
        self.logger_name = logger_name
        # self.stream_handler.setFormatter(Out_formatter_type.custom_formatter)
        # self.file_handler.setFormatter(Out_formatter_type.custom_formatter)
        self.logger = logging.getLogger(name=self.logger_name)
        self.logger.setLevel(level)
        self.logger.addHandler(self.stream_handler)
        self.logger.addHandler(self.file_handler)
        # 关闭日志向上级logger传递
        self.logger.propagate = False
        LoggerManager.instance_dict[logger_name] = self

    def writelog(
        self,
        content: str,
        out_formatter_type: Out_formatter_type = Out_formatter_type.custom_formatter,
        out_type: OutType = OutType.info,
        flush: bool = False,
        user_defined_formatter_str: str = None,
    ):
        """
        Args:
            content:要输出的内容
            out_formatter_type：输出的格式
                Out_formatter_type.custom_formatter:通用格式（带时间、level、日志器名称）
                Out_formatter_type.plain_formatter:无格式，直接输出内容
                Out_formatter_type.time_formatter:时间+内容格式
                Out_formatter_type.user_defined_formatter:用户自定义格式
            out_type:以哪种级别产生日志
                OutType.debug、OutType.info、OutType.warning、OutType.error、OutType.critical
            flush:控制到保存到文件中的日志是否立即写入。是指立即刷新到硬盘，不是刷新到屏幕！
                True:立即写入
                False:延迟写入
            user_defined_formatter_str:输出的格式（整体格式与时间格式用逗号','分隔，也可以不写时间格式，用系统默认时间格式）
        """
        # 根据枚举值设置处理器格式
        if out_formatter_type == Out_formatter_type.custom_formatter:
            self.stream_handler.setFormatter(Custom_formatter)
            self.file_handler.setFormatter(Custom_formatter)
        elif out_formatter_type == Out_formatter_type.plain_formatter:
            self.stream_handler.setFormatter(Plain_formatter)
            self.file_handler.setFormatter(Plain_formatter)
        elif out_formatter_type == Out_formatter_type.time_formatter:
            self.stream_handler.setFormatter(Time_formatter)
            self.file_handler.setFormatter(Time_formatter)
        elif out_formatter_type == Out_formatter_type.user_defined_formatter:
            if user_defined_formatter_str is None:
                raise ValueError(
                    "out_formatter_type为Out_formatter_type.user_defined_formatter时，\
                    参数'user_defined_formatter_str'不能为空！"
                )
            # 用户可以用一条字符串同时传入输出整体格式与时间格式。用逗号","分隔！程序收到后先做分割！
            spilt_list = user_defined_formatter_str.split(",", maxsplit=1)
            if len(spilt_list) == 2:
                fmt = spilt_list[0]
                datefmt = spilt_list[1]
                self.stream_handler.setFormatter(logging.Formatter(fmt, datefmt))
                self.file_handler.setFormatter(logging.Formatter(fmt, datefmt))
            else:
                fmt = fmt = spilt_list[0]
                self.stream_handler.setFormatter(logging.Formatter(fmt))
                self.file_handler.setFormatter(logging.Formatter(fmt))

        log_func = getattr(self.logger, out_type.value)
        log_func(content)
        if flush:
            self.file_handler.flush()

    @classmethod
    def set_custom_formatter(cls, fmt: str, datefmt: str):
        """
        设置修改处理器通用格式的具体格式，以及时间格式
        Args:
            fmt:输出格式字符串
            datefmt:时间格式字符串
        """
        global Custom_formatter
        Custom_formatter = logging.Formatter(fmt, datefmt)

    @classmethod
    def set_time_formatter(cls, datefmt: str):
        """
        设置修改处理器时间格式的具体时间格式
        Args:
            datefmt:时间格式字符串
        """
        global Time_formatter
        Time_formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt)
