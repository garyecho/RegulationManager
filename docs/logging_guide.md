# 日志系统使用指南

## 概述

制度汇编管理系统配备了完善的日志记录功能，帮助开发者和管理员追踪系统运行状态、诊断问题和审计用户操作。

## 日志文件位置

- **日志目录**：`data/logs/`
- **日志文件**：`app_YYYYMMDD.log`（按日期自动分割）
- **日志格式**：`YYYY-MM-DD HH:MM:SS [级别] 模块名: 消息内容`

## 日志级别说明

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发调试时使用，生产环境通常关闭 |
| INFO | 普通信息 | 记录正常操作流程和状态变化 |
| WARNING | 警告信息 | 不影响运行但需要注意的问题 |
| ERROR | 错误信息 | 功能执行失败，需要排查 |
| CRITICAL | 严重错误 | 系统级错误，可能导致应用崩溃 |

## 日志查看方法

### 方法一：通过系统界面查看（推荐）

1. 启动应用程序
2. 菜单栏 → **工具** → **查看系统日志**（快捷键：Ctrl+L）
3. 在日志查看器中可以：
   - 选择不同的日志文件
   - 按日志级别过滤
   - 按关键词搜索
   - 导出日志内容
   - 清理旧日志文件

### 方法二：直接查看日志文件

1. 打开文件资源管理器
2. 导航到程序目录下的 `data/logs/` 文件夹
3. 使用文本编辑器（如记事本、Notepad++）打开日志文件

### 方法三：命令行查看（开发者）

```bash
# 查看今天的日志
type data\logs\app_%date:~0,4%%date:~5,2%%date:~8,2%.log

# 查看最近的错误日志
findstr /C:"[ERROR]" data\logs\app_*.log

# 实时监控日志（需要 PowerShell）
Get-Content data\logs\app_*.log -Wait
```

## 日志内容说明

### 系统启动日志
```
2024-01-15 09:30:15 [INFO] __main__: 启动 制度汇编管理系统 v1.3.1
2024-01-15 09:30:16 [INFO] database.migrations: 数据库初始化完成
```

### 用户操作日志
```
2024-01-15 09:31:20 [INFO] core.document_service: 开始上传文档：关于加强内部控制的通知
2024-01-15 09:31:22 [INFO] core.document_service: 文档已保存到数据库，ID：125
2024-01-15 09:31:22 [INFO] core.document_service: 成功导入：关于加强内部控制的通知
```

### 批量操作日志
```
2024-01-15 09:35:10 [INFO] core.document_service: 开始批量导入，文件数量：25，跳过重复：True
2024-01-15 09:35:15 [INFO] core.document_service: 跳过重复文件：关于风险管理的规定.docx
2024-01-15 09:35:18 [INFO] core.document_service: 成功导入：关于加强合规管理的通知
2024-01-15 09:40:30 [INFO] core.document_service: 批量导入完成，成功：20，失败：2，跳过：3
```

### 错误日志示例
```
2024-01-15 10:15:30 [ERROR] core.document_service: 导入失败 D:\docs\test.pdf: 文件损坏，无法读取
2024-01-15 10:15:31 [WARNING] utils.text_extractor: 提取文档正文失败：不支持的文件格式
```

## 常见问题排查

### 1. 应用启动失败

查看日志中的启动序列：
```
[INFO] __main__: 启动 制度汇编管理系统 v1.3.1
[ERROR] database.migrations: 数据库初始化失败: ...
```

### 2. 文档导入失败

搜索相关文档名称或错误关键词：
```
[ERROR] core.document_service: 导入失败 xxx: 具体错误信息
```

### 3. 搜索功能异常

检查索引相关日志：
```
[WARNING] utils.search_engine: FTS5 索引写入失败: ...
[INFO] utils.search_engine: 重建搜索索引完成，索引文档数：xxx
```

### 4. 性能问题

查找耗时较长的操作：
```
[WARNING] 性能警告：批量导入 耗时 45.23秒 文件数量：100
```

## 日志管理建议

### 1. 定期清理日志
- 通过系统界面的"清理旧日志"功能
- 建议保留30天以内的日志
- 重要操作前可手动备份日志文件

### 2. 监控错误日志
- 定期检查 `[ERROR]` 和 `[CRITICAL]` 级别的日志
- 关注重复出现的错误模式

### 3. 导出重要日志
- 遇到问题时导出相关时间段的日志
- 提交bug报告时附上日志文件

### 4. 日志文件大小管理
- 系统自动进行日志轮转（单个文件最大10MB）
- 保留最近10个日志文件
- 超出会自动删除最旧的日志

## 技术细节

### 日志配置
- 日志级别：INFO（可通过代码调整为DEBUG获取更详细信息）
- 文件编码：UTF-8
- 轮转策略：大小轮转（10MB）+ 数量限制（10个）
- 备份文件：`app_YYYYMMDD.log.1`, `.log.2`, 等

### 性能影响
- 日志记录对系统性能影响极小
- 文件日志使用缓冲写入，减少I/O开销
- 控制台日志在打包版本中默认关闭

## 开发者指南

### 添加自定义日志

在代码中添加日志记录：

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("开始执行操作")
    try:
        # 业务逻辑
        result = do_something()
        logger.info("操作成功完成，结果：%s", result)
        return result
    except Exception as e:
        logger.error("操作失败：%s", str(e), exc_info=True)
        raise
```

### 使用日志装饰器

```python
from utils.log_manager import log_operation

@log_operation("文档上传", "单个文件")
def upload_document(file_path):
    # 上传逻辑
    pass
```

### 性能监控

```python
import time
from utils.log_manager import log_performance

start_time = time.time()
# 执行耗时操作
duration = time.time() - start_time
log_performance("批量导入", duration, f"文件数量：{len(files)}")
```

## 联系支持

如果通过日志仍无法解决问题，请：
1. 导出问题发生时段的日志文件
2. 记录问题重现步骤
3. 联系技术支持并提供以上信息

技术支持将通过日志精准定位问题根源，提供针对性的解决方案。