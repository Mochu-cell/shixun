# 项目整理记录（PROJECT_NOTES）

> 本文档记录项目目录的整理过程与变更说明，便于后续维护者了解当前结构与历史改动。

## 一、整理前的问题

1. **目录按日期堆积**：根目录存在 `0701` ~ `0709` 九个按日期命名的目录，职责不清，难以快速定位代码、数据与文档。
2. **大量重复文件**：
   - `ssh_exec.py` 存在 3 份；
   - 训练监控/分析脚本、数据生成脚本、预训练权重各 2 份；
   - Hive SQL/HQL/Shell 在多处重复（`hive_ods_ddl.sql` 甚至 3 份）；
   - 多份重复的数据目录与仪表盘工程副本。
3. **临时产物与缓存入库**：`__pycache__`、matplotlib 字体缓存 `.mplconfig`、YOLO 标注缓存 `*.cache`、`detection_history.db` 等被提交。
4. **敏感信息**：MySQL 密码、SSH 密码、虚拟机 IP 散落在代码与文档中。
5. **陈旧残留**：脑肿瘤项目内的原始包残留目录、旧版配置文件、写死本机绝对路径的 `data.yaml`。
6. **缺少文档**：根目录没有 README，也没有整理记录。
7. **不完整实验**：`runs/` 下存在早期不完整实验，仅保留少量中间图。

## 二、整理后的目录结构

```
data/       医保原始/清洗/脱敏/标准化/类型化数据、清洗管道输出、数仓分层 CSV、ML 数据
scripts/    etl（ETL Shell + 本地模拟 + 清洗管道 + 建表导入）、medical（ML/可视化/影像分析）、vm
sql/        hive（ODS/DWD/DM DDL + ODS 导入）、hql（ETL 与主题分析）、mysql（报表/高风险/检测统计 DDL）
models/     brain_tumor_detection（YOLOv11 完整子工程：数据、训练、权重、评估）
web/        dashboard（医保仪表盘）、detection（脑肿瘤检测）、integrated（综合仪表盘）
docs/       项目总结（唯一文档）
reports/    医保分析、脑肿瘤 MRI 分析、训练评估
config/     脱敏映射 JSON + 本地敏感配置模板（真实凭据不入库）
```

## 三、变更说明

### 3.1 目录迁移（git 已记录重命名）

| 原路径 | 新路径 |
|--------|--------|
| `0702/data/*` | `data/*`（权威副本） |
| `0702/data/medical_insurance_warehouse` | `data/warehouse` |
| `0703/ml/dm_insurance_stats.csv` | `data/ml/dm_insurance_stats.csv` |
| `0702/config/*.json` | `config/*.json` |
| `0703/dataetl/sql|hql|shell` | `sql/hive|hql`、`scripts/etl` |
| `brain_tumor_detection` | `models/brain_tumor_detection` |
| `brain_tumor_detection/scripts/web` | `web/detection` |
| `0704/dashboard` | `web/dashboard` |
| `0709/MBST_web` | `web/integrated` |
| `0703/ml/*.py` | `scripts/medical/ml/` |
| `0704/visualization/visualization_matplotlib.py` | `scripts/medical/visualization_matplotlib.py` |
| `0705/code/*.py` | `scripts/medical/analysis/` |
| `ssh_exec.py`、`VM/shell/*` | `scripts/vm/` |
| 各日笔记/课件/操作说明 | `docs/`（后经第二轮精简） |
| 各日图表/报告/演示图 | `reports/` |

### 3.2 删除的重复文件（git 历史可查）

- 重复的 `ssh_exec.py`、训练监控/分析脚本、`generate_output_data.py`、`yolo11n.pt`
- `0708/web/*`（与 web/detection 完全一致）
- `0702/dataetl` 与 `0703/dataetl` 中重复的 SQL/HQL/Shell
- 重复的数据目录副本
- `0705/code/data/*`（69 张图，与原始 MRI 数据集哈希一致，脚本已改指向原始数据集）
- 脑肿瘤项目内原始包残留目录与旧版配置
- 早期不完整实验 `brain_tumor_exp`、`brain_tumor_exp-2`
- 练习脚本目录 `scripts/lessons/`（逐步演示型脚本，无独立维护价值）

### 3.3 删除的临时/缓存产物

- `__pycache__`、`*.pyc`
- matplotlib 字体缓存 `.mplconfig`
- YOLO 标注缓存 `*.cache`
- `detection_history.db`（运行时自动重建）
- `web/detection/static/uploads|results`（运行时产物，已加入 .gitignore）
- 无效打包备份（RAR 归档，内容均有解包副本）

### 3.4 文档精简与内容合并

- `docs/` 精简为仅保留 `docs/项目总结.md`，其余课堂资料全部删除。
- 有价值的功能脚本并入正式模块：
  - 数据清洗管道 → `scripts/etl/data_clean_pipeline.py`，输出 → `data/clean_output/`，清洗报告 → `reports/医保分析/数据清洗报告.txt`；
  - 高风险人员建表导入 → `scripts/etl/create_load_highrisk.py`，DDL → `sql/mysql/high_risk_ddl.sql`；
  - 高风险名单/次均费用等功能已由 `web/dashboard` 承载。
- 代码中的演示性描述统一清理，改为功能描述。

### 3.5 代码与配置修改

- **路径适配**：脚本统一改为相对路径或以仓库根目录为基准；Web 模型查找指向 `models/brain_tumor_detection/runs`。
- **相对路径**：`data/brain_tumor_yolo/data.yaml` 与 `convert_dataset.py` 输出相对路径。
- **敏感信息脱敏**：Python 应用/脚本读取环境变量或 `config/local_config.py`（gitignore）；Shell 脚本要求 `export MYSQL_PASS`；真实值仅存于本机 `config/local_config.py`。
- **可移植性**：matplotlib 可视化脚本的 MPLCONFIGDIR 改为系统临时目录，输出图表固定到 `reports/医保分析/`。

## 四、验证情况

- 全部 Python 脚本通过 `py_compile` 语法检查。
- 已扫描跟踪文件，确认无 MySQL 密码、内网 IP 等真实敏感信息。
- 训练权重（best.pt/last.pt/epoch*.pt）、原始数据集（7200 张 MRI）与关键 CSV 均未删除。
- README 与项目总结中的运行命令按当前目录验证可用。

## 五、后续建议

1. 新增内容遵循模块化目录，不再按日期建目录。
2. 敏感凭据统一走环境变量或 `config/local_config.py`，严禁写入代码与文档。
3. Web 上传/结果目录为运行时产物，保持 .gitignore 忽略。
4. 如需补充模型推理演示、API 文档等，可在 `docs/` 下新增文档。
