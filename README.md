# 医疗医保大数据与脑肿瘤影像智能检测系统

## 项目简介

本项目是一个医疗医保大数据分析与脑肿瘤影像智能检测系统，将**医保大数据分析**与**脑肿瘤 MRI 影像智能检测**两大模块整合为完整闭环：

- **医保大数据模块**：以参保人、就诊记录、费用明细三张原始 CSV 为基础，完成数据清洗、脱敏、标准化，并通过 Hive/Spark SQL 构建 **ODS → DWD → DM** 三层数仓，输出 12 个分析主题，最终以 Flask + ECharts 仪表盘呈现医保 KPI、月度趋势、医院热力图、高风险人员名单等。
- **脑肿瘤检测模块**：基于 **YOLOv11** 对 7200 张脑肿瘤 MRI 图像（胶质瘤/脑膜瘤/无肿瘤/垂体瘤四类）进行目标检测训练，mAP50 达 99.5%，并提供 Flask 图像上传检测 Web 系统与综合仪表盘。

> 项目总览与交接说明见 [docs/项目总结.md](docs/项目总结.md)；本次目录整理的变更记录见 [PROJECT_NOTES.md](PROJECT_NOTES.md)。

## 技术栈

| 类别 | 技术 |
|------|------|
| 大数据存储/计算 | Hadoop/HDFS、Hive、Spark SQL（3.5.2） |
| 关系数据库 | MySQL 8.0（报表层 + Hive 元数据库） |
| 数据处理 | Python/PySpark、pandas、numpy |
| 机器学习 | Spark MLlib（异常检测、费用预测） |
| 深度学习 | PyTorch、Ultralytics YOLOv11 |
| 图像处理 | OpenCV、Matplotlib |
| Web | Flask、ECharts、HTML/CSS/JavaScript、SQLite |
| 操作系统 | Windows 11（主机）、CentOS 7（虚拟机） |

## 系统架构

```
┌────────────────────────────────────────────────────────────┐
│  前端层  HTML + CSS + JavaScript + ECharts（仪表盘/检测页）    │
├────────────────────────────────────────────────────────────┤
│  后端层  Flask（web/dashboard、web/detection、web/integrated）│
├────────────────────────────────────────────────────────────┤
│  模型层  YOLOv11 脑肿瘤检测（models/brain_tumor_detection）   │
│          Spark MLlib 医保异常检测 / 费用预测                   │
├────────────────────────────────────────────────────────────┤
│  数据层  HDFS / Hive(ODS·DWD·DM) / MySQL / SQLite           │
└────────────────────────────────────────────────────────────┘
```

## 数据流

### 医保大数据流

```
原始三表 CSV（参保/就诊/费用）
    ↓ 清洗、脱敏、标准化
data/medical_insurance（ODS 源数据）
    ↓ Hive ODS 建表 + LOAD（sql/hive、scripts/etl/01_hive_ods_init.sh）
ODS 层：ods_insurance_info / ods_medical_record / ods_expense_detail
    ↓ ODS→DWD 三表 JOIN + 字段衍生（sql/hql/etl_ods_to_dwd.hql）
DWD 层：dwd_insurance_detail 明细宽表（按日分区）
    ↓ DWD→DM 聚合（sql/hql/etl_dwd_to_dm.hql）
DM 层：dm_insurance_stats / dm_hospital_stats / dm_cost_analysis / dm_reimburse_analysis
    ↓ 导出 CSV + LOAD 到 MySQL（scripts/etl/04_export_tomysql.sh）
MySQL 报表层：rpt_insurance_stats / rpt_hospital_stats / rpt_cost_analysis / rpt_reimburse_analysis
    ↓ Flask API
医保仪表盘（web/dashboard）与综合仪表盘（web/integrated）
```

### 脑肿瘤检测流

```
原始 MRI 数据集（data/raw/Training、Testing）
    ↓ convert_dataset.py 转换为 YOLO 格式（7:2:1 划分）
YOLO 数据集（data/brain_tumor_yolo）
    ↓ start_training.py 训练（YOLOv11n，50 epochs）
最佳权重（runs/.../weights/best.pt，mAP50 99.5%）
    ↓ Flask 推理接口（web/detection）
图像上传 → 检测框可视化 → SQLite 历史记录
    ↓ generate_output_data.py 生成统计 TXT → MySQL（tumor_* 4 张表）
综合仪表盘（web/integrated，端口 5002）
```

## Hive 数仓分层

| 分层 | 库名 | 表 | 说明 |
|------|------|-----|------|
| ODS | `ods` | ods_insurance_info、ods_medical_record、ods_expense_detail | 原始三表，与 CSV 1:1 映射，按日分区 |
| DWD | `dwd` | dwd_insurance_detail | 三表 JOIN 宽表，衍生年龄段/参保月数/医院等级/报销率等 |
| DM | `dm` | dm_insurance_stats、dm_hospital_stats、dm_cost_analysis、dm_reimburse_analysis | 参保人/医院/月度/报销四维聚合 |
| 报表 | MySQL `data` | rpt_* 4 张 + high_risk_person + tumor_* 4 张 | 供仪表盘与高风险分析使用 |

## 环境搭建

### 1. 主机（Windows）

- Python 3.11 + Miniconda（推荐创建独立 conda 环境）
- 医保分析：`pip install pandas numpy matplotlib flask pymysql scikit-learn opencv-python`
- YOLO 训练（conda 环境 `yolo`）：`pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124`，再 `pip install ultralytics opencv-python pandas matplotlib flask pyyaml`

### 2. 虚拟机（CentOS 7）

- 已安装 Hadoop、Spark 3.5.2、Hive（经 Spark SQL）、MySQL 8.0、Python 3.8，详见 [docs/项目总结.md](docs/项目总结.md)。
- 注意：Hive 操作必须用 `hadoop` 用户执行 `spark-sql`；HDFS 进程需 `root` 启动。

### 3. 敏感信息配置（重要）

本仓库**不提交**任何密码/IP。运行涉及 MySQL 或虚拟机的脚本前，请按以下任一方式配置：

1. 复制 `config/local_config.example.py` 为 `config/local_config.py` 并填写真实值（该文件已被 .gitignore 忽略）；
2. 或设置环境变量：`MYSQL_HOST`、`MYSQL_PORT`、`MYSQL_USER`、`MYSQL_PASSWORD`、`MYSQL_DATABASE`、`VM_HOST`、`VM_USER`、`VM_PASSWORD`；
3. Shell 脚本（`scripts/etl/*.sh`、`scripts/vm/*.sh`）请先 `export MYSQL_PASS=<你的MySQL密码>`。

## YOLO 训练与评估

```powershell
cd models/brain_tumor_detection
conda activate yolo

python scripts/convert_dataset.py   # 数据集转换（原始 → YOLO 格式，已转换可跳过）
python scripts/env_setup.py         # 环境检查（6 项）
python scripts/train_config.py      # 生成训练配置 configs/training_config.yaml
$env:KMP_DUPLICATE_LIB_OK="TRUE"    # 如遇 OMP 报错则启用
python scripts/start_training.py    # 启动训练

# 训练监控与评估
python scripts/monitor_training.py  # 训练曲线
python scripts/analyze_loss.py      # Loss 分析
python scripts/analyze_results.py   # 指标分析（P/R/mAP）
```

训练结果（models/brain_tumor_detection/runs/）：

| 指标 | 数值 |
|------|------|
| mAP50 | 99.50% |
| mAP50-95 | 99.49% |
| Precision | 99.52% |
| Recall | 99.57% |
| 轮数 | 50 |

CPU 用户请修改 `configs/training_config.yaml`：`device: cpu`、`batch: 4`、`epochs: 5`、`imgsz: 320`。

## Web 系统

| 应用 | 目录 | 端口 | 说明 |
|------|------|------|------|
| 医保仪表盘 | web/dashboard | 5000 | 医保 KPI、月度趋势、医院热力图、高风险名单 |
| 脑肿瘤检测 | web/detection | 5001 | MRI 图像上传、YOLO 推理、结果可视化、历史记录 |
| 综合仪表盘 | web/integrated | 5002 | 医保 + 脑肿瘤检测数据整合展示 |

```powershell
# 医保仪表盘
cd web/dashboard
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
python app.py

# 脑肿瘤检测（需 ultralytics + 训练权重）
cd web/detection
python app.py

# 综合仪表盘
cd web/integrated
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
python app.py
```

浏览器访问 `http://localhost:5000 / 5001 / 5002`。

## 运行命令速查

### 本地 ETL 模拟（无需 Hadoop）

```powershell
python scripts/etl/local_etl_simulation.py
```

### 虚拟机 ETL（Hive/Spark）

```bash
cd /home/hadoop
export MYSQL_PASS=<你的MySQL密码>
bash scripts/etl/01_hive_ods_init.sh 20260702          # ODS 建表 + 导入
bash scripts/etl/02_etl_ods_to_dwd.sh 20260702         # ODS → DWD
bash scripts/etl/03_etl_dwd_to_dm_analysis.sh 20260702 # DWD → DM + 主题分析
bash scripts/etl/04_export_tomysql.sh 20260702 data    # 导出并导入 MySQL
```

### 生成脑肿瘤检测统计数据并导入 MySQL

```powershell
cd models/brain_tumor_detection
python scripts/generate_output_data.py   # 生成 data/output/*.txt
```

将 `data/output` 与 `scripts/etl/import_to_mysql.sh` 上传到虚拟机后执行：

```bash
export MYSQL_PASS=<你的MySQL密码>
sh import_to_mysql.sh
```

### 虚拟机远程执行

```powershell
python scripts/vm/ssh_exec.py "命令内容"
python scripts/vm/ssh_exec.py -f scripts/vm/某个脚本.sh
```

## 目录说明

```
shixun/
├── data/                  医保原始/清洗/脱敏/标准化/类型化数据、清洗管道输出、数仓分层 CSV、ML 数据
├── scripts/
│   ├── etl/               Hive/Spark ETL Shell、本地 ETL 模拟、数据清洗管道、建表导入脚本
│   ├── medical/           Spark ML（异常检测/费用预测）、Matplotlib 可视化、OpenCV 分析
│   └── vm/                虚拟机 SSH 执行器、MySQL 修复/导入脚本
├── sql/
│   ├── hive/              ODS/DWD/DM 建表 DDL 与 ODS 导入 SQL
│   ├── hql/               ODS→DWD、DWD→DM、Spark 主题分析 HQL
│   └── mysql/             MySQL 报表 DDL、高风险人员表 DDL、检测统计表 DDL
├── models/
│   └── brain_tumor_detection/   YOLOv11 完整子工程（数据、训练、权重、评估）
│       ├── data/          原始 MRI 数据集 + YOLO 格式数据集 + 输出统计
│       ├── scripts/       转换/环境检查/训练/监控/分析/数据生成脚本
│       ├── configs/       训练参数配置
│       └── runs/          训练输出（weights/best.pt、曲线、指标 CSV）
├── web/
│   ├── dashboard/         医保仪表盘（Flask + ECharts）
│   ├── detection/         脑肿瘤检测 Web（YOLO 推理）
│   └── integrated/        医保 + 脑肿瘤综合仪表盘
├── docs/                  项目总结（唯一文档）
├── reports/               医保分析图、脑肿瘤 MRI 分析报告与图表、训练评估演示图
├── config/                脱敏映射配置 + 本地敏感配置模板（真实凭据不入库）
├── README.md              本文件
└── PROJECT_NOTES.md       目录整理记录与变更说明
```

## GitHub 地址

- 仓库地址：<https://github.com/Mochu-cell/shixun.git>
- 分支：main

## 其他说明

- 所有文档与代码注释均为中文，文件编码 UTF-8。
- 训练权重、原始 MRI 数据集等关键文件已保留；`models/brain_tumor_detection/runs/` 下的完整实验（exp-3）为最终结果，未做删减。
