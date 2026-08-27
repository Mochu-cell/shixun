#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医保异常行为识别（Spark MLlib）
使用Spark MLlib实现分类算法（逻辑回归、决策树、随机森林）

运行方式：
  spark-submit ml_abnormal_detection.py

数据格式说明：
  dm_insurance_stats.csv 使用 | 分隔符，无列名
  列顺序：person_id|age_group|insurance_type|visit_count|total_amount|reimburse_amount|reimburse_rate|avg_visit_amount|first_visit_date|last_visit_date|etl_date
"""

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression, DecisionTreeClassifier, RandomForestClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
from pyspark.sql.functions import col, when, lit, abs as spark_abs
import os

print("=" * 60)
print("  医保异常行为识别（Spark MLlib）")
print("=" * 60)

# ============================================================
# Step 1: 创建SparkSession
# ============================================================
print("\n[Step 1] 创建SparkSession...")

spark = SparkSession.builder \
    .appName("AbnormalDetection") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
print("  SparkSession创建成功")

# ============================================================
# Step 2: 加载特征数据
# ============================================================
print("\n[Step 2] 加载特征数据...")

# 数据路径
DATA_DIR = "/home/hadoop/temp/analysis_results"
LOCAL_PATH = os.path.join(DATA_DIR, "dm_insurance_stats.csv")
DATA_PATH = f"file://{LOCAL_PATH}"

# 定义列名（对应CSV的实际列顺序）
COLUMN_NAMES = [
    "person_id",
    "age_group",
    "insurance_type",
    "visit_count",
    "total_amount",
    "reimburse_amount",
    "reimburse_rate",
    "avg_visit_amount",
    "first_visit_date",
    "last_visit_date",
    "etl_date"
]

# 检查文件是否存在
if not os.path.exists(LOCAL_PATH):
    print("  [警告] 数据文件不存在，生成模拟数据")
    
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    n_samples = 500
    
    mock_data = pd.DataFrame({
        'person_id': [f'P{str(i).zfill(6)}' for i in range(1, n_samples+1)],
        'age_group': np.random.choice(['0-18', '19-35', '36-55', '56-70', '70+'], n_samples),
        'insurance_type': np.random.choice(['城镇职工', '城镇居民', '新农合', '灵活就业'], n_samples),
        'visit_count': np.random.randint(1, 20, n_samples),
        'avg_visit_amount': np.random.uniform(500, 5000, n_samples),
        'reimburse_rate': np.random.uniform(0.3, 0.9, n_samples)
    })
    
    mock_data['total_amount'] = mock_data['visit_count'] * mock_data['avg_visit_amount']
    mock_data['reimburse_amount'] = mock_data['total_amount'] * mock_data['reimburse_rate']
    
    # 创建异常标签
    mock_data['is_abnormal'] = (
        (mock_data['visit_count'] > 12) |
        (mock_data['avg_visit_amount'] > 6000) |
        (mock_data['reimburse_rate'] > 0.9)
    ).astype(int)
    
    # 添加异常样本
    for _ in range(25):
        idx = np.random.randint(n_samples)
        mock_data.loc[idx, 'visit_count'] = np.random.randint(15, 30)
        mock_data.loc[idx, 'avg_visit_amount'] = np.random.uniform(8000, 15000)
        mock_data.loc[idx, 'reimburse_rate'] = np.random.uniform(0.92, 0.99)
    
    os.makedirs(DATA_DIR, exist_ok=True)
    mock_data.to_csv(LOCAL_PATH, sep='|', header=False, index=False)
    print(f"  模拟数据已保存: {LOCAL_PATH}")
else:
    print(f"  使用现有数据: {LOCAL_PATH}")

# 加载CSV - 使用|分隔符，无header，手动指定列名
df = spark.read.csv(
    DATA_PATH,
    header=False,        # 无列名
    sep='|',             # | 分隔符
    inferSchema=True     # 自动推断类型
)

# 设置列名
for i, col_name in enumerate(COLUMN_NAMES):
    df = df.withColumnRenamed(f'_c{i}', col_name)

print(f"  数据加载完成: {df.count()}条记录")
print(f"  列名: {df.columns}")

# 显示数据样例
print("\n  数据样例:")
df.show(5)

# ============================================================
# Step 3: 创建异常标签
# ============================================================
print("\n[Step 3] 创建异常标签...")

# 清洗数据：过滤异常值
df = df.filter(col('total_amount') > 0)
df = df.filter(col('avg_visit_amount') > 0)

# 基于规则创建异常标签
# 规则：就诊次数>12 或 单次费用>6000 或 报销率>0.9 或 总费用异常高
df = df.withColumn('is_abnormal',
    when((col('visit_count') > 12) |
         (col('avg_visit_amount') > 6000) |
         (col('reimburse_rate') > 0.9) |
         (col('total_amount') > 50000), 1)
    .otherwise(0)
)

# 统计异常样本
abnormal_count = df.filter(col('is_abnormal') == 1).count()
normal_count = df.filter(col('is_abnormal') == 0).count()
print(f"  正常样本: {normal_count}")
print(f"  异常样本: {abnormal_count}")
print(f"  异常比例: {abnormal_count/(normal_count+abnormal_count)*100:.2f}%")

# ============================================================
# Step 4: 特征预处理Pipeline
# ============================================================
print("\n[Step 4] 构建特征预处理Pipeline...")

# 假设参保时间
df = df.withColumn('enroll_months', lit(12))

# StringIndexer
age_indexer = StringIndexer(inputCol="age_group", outputCol="age_encoded", handleInvalid="keep")
insurance_indexer = StringIndexer(inputCol="insurance_type", outputCol="insurance_encoded", handleInvalid="keep")

# 数值特征
feature_cols = ["age_encoded", "insurance_encoded", "enroll_months", "visit_count", "avg_visit_amount", "reimburse_rate"]

# VectorAssembler
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")

# StandardScaler
scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=False)

pipeline_stages = [age_indexer, insurance_indexer, assembler, scaler]
preprocess_pipeline = Pipeline(stages=pipeline_stages)
print("  Pipeline构建完成")

# ============================================================
# Step 5: 划分数据集
# ============================================================
print("\n[Step 5] 划分训练集和测试集...")

preprocess_model = preprocess_pipeline.fit(df)
df_processed = preprocess_model.transform(df)

train_data, test_data = df_processed.randomSplit([0.8, 0.2], seed=42)

print(f"  训练集: {train_data.count()}条")
print(f"  测试集: {test_data.count()}条")

# ============================================================
# Step 6: 逻辑回归分类
# ============================================================
print("\n[Step 6] 逻辑回归分类模型...")

lr = LogisticRegression(
    featuresCol="scaled_features",
    labelCol="is_abnormal",
    predictionCol="lr_prediction",
    rawPredictionCol="lr_raw",
    probabilityCol="lr_prob",
    maxIter=100
)

lr_model = lr.fit(train_data)
lr_predictions = lr_model.transform(test_data)

print("  逻辑回归模型训练完成")

print("\n  逻辑回归预测样例:")
lr_predictions.select("person_id", "age_group", "visit_count", "avg_visit_amount", "is_abnormal", "lr_prediction", "lr_prob").show(5)

# ============================================================
# Step 7: 决策树分类
# ============================================================
print("\n[Step 7] 决策树分类模型...")

dt = DecisionTreeClassifier(
    featuresCol="scaled_features",
    labelCol="is_abnormal",
    predictionCol="dt_prediction",
    probabilityCol="dt_prob",
    maxDepth=5,
    seed=42
)

dt_model = dt.fit(train_data)
dt_predictions = dt_model.transform(test_data)
# 手动重命名rawPrediction列（DecisionTree不支持自定义rawPredictionCol）
dt_predictions = dt_predictions.withColumnRenamed("rawPrediction", "dt_raw")

print("  决策树模型训练完成")

print("\n  决策树预测样例:")
dt_predictions.select("person_id", "age_group", "visit_count", "avg_visit_amount", "is_abnormal", "dt_prediction", "dt_prob").show(5)

# ============================================================
# Step 8: 随机森林分类
# ============================================================
print("\n[Step 8] 随机森林分类模型...")

rf = RandomForestClassifier(
    featuresCol="scaled_features",
    labelCol="is_abnormal",
    predictionCol="rf_prediction",
    probabilityCol="rf_prob",
    numTrees=50,
    maxDepth=8,
    seed=42
)

rf_model = rf.fit(train_data)
rf_predictions = rf_model.transform(test_data)
# 手动重命名rawPrediction列（RandomForest不支持自定义rawPredictionCol）
rf_predictions = rf_predictions.withColumnRenamed("rawPrediction", "rf_raw")

print("  随机森林模型训练完成")

print("\n  随机森林预测样例:")
rf_predictions.select("person_id", "age_group", "visit_count", "avg_visit_amount", "is_abnormal", "rf_prediction", "rf_prob").show(5)

# ============================================================
# Step 9: 模型评估对比
# ============================================================
print("\n[Step 9] 模型评估对比...")

# AUC评估器
auc_evaluator = BinaryClassificationEvaluator(
    labelCol="is_abnormal",
    rawPredictionCol="lr_raw",
    metricName="areaUnderROC"
)

# 多分类评估器
f1_evaluator = MulticlassClassificationEvaluator(labelCol="is_abnormal", predictionCol="lr_prediction", metricName="f1")
accuracy_evaluator = MulticlassClassificationEvaluator(labelCol="is_abnormal", predictionCol="lr_prediction", metricName="accuracy")
precision_evaluator = MulticlassClassificationEvaluator(labelCol="is_abnormal", predictionCol="lr_prediction", metricName="weightedPrecision")
recall_evaluator = MulticlassClassificationEvaluator(labelCol="is_abnormal", predictionCol="lr_prediction", metricName="weightedRecall")

# 评估逻辑回归
lr_auc = auc_evaluator.evaluate(lr_predictions)
lr_f1 = f1_evaluator.evaluate(lr_predictions)
lr_accuracy = accuracy_evaluator.evaluate(lr_predictions)
lr_precision = precision_evaluator.evaluate(lr_predictions)
lr_recall = recall_evaluator.evaluate(lr_predictions)

# 评估决策树
auc_evaluator.setRawPredictionCol("dt_raw")
dt_auc = auc_evaluator.evaluate(dt_predictions)
f1_evaluator.setPredictionCol("dt_prediction")
dt_f1 = f1_evaluator.evaluate(dt_predictions)
accuracy_evaluator.setPredictionCol("dt_prediction")
dt_accuracy = accuracy_evaluator.evaluate(dt_predictions)
precision_evaluator.setPredictionCol("dt_prediction")
dt_precision = precision_evaluator.evaluate(dt_predictions)
recall_evaluator.setPredictionCol("dt_prediction")
dt_recall = recall_evaluator.evaluate(dt_predictions)

# 评估随机森林
auc_evaluator.setRawPredictionCol("rf_raw")
rf_auc = auc_evaluator.evaluate(rf_predictions)
f1_evaluator.setPredictionCol("rf_prediction")
rf_f1 = f1_evaluator.evaluate(rf_predictions)
accuracy_evaluator.setPredictionCol("rf_prediction")
rf_accuracy = accuracy_evaluator.evaluate(rf_predictions)
precision_evaluator.setPredictionCol("rf_prediction")
rf_precision = precision_evaluator.evaluate(rf_predictions)
recall_evaluator.setPredictionCol("rf_prediction")
rf_recall = recall_evaluator.evaluate(rf_predictions)

print("\n" + "=" * 70)
print("  模型对比结果")
print("=" * 70)
print(f"\n  {'模型':<12} {'AUC':<8} {'Accuracy':<10} {'F1':<8} {'Precision':<10} {'Recall':<10}")
print(f"  {'逻辑回归':<12} {lr_auc:<8.4f} {lr_accuracy:<10.4f} {lr_f1:<8.4f} {lr_precision:<10.4f} {lr_recall:<10.4f}")
print(f"  {'决策树':<12} {dt_auc:<8.4f} {dt_accuracy:<10.4f} {dt_f1:<8.4f} {dt_precision:<10.4f} {dt_recall:<10.4f}")
print(f"  {'随机森林':<12} {rf_auc:<8.4f} {rf_accuracy:<10.4f} {rf_f1:<8.4f} {rf_precision:<10.4f} {rf_recall:<10.4f}")

# ============================================================
# Step 10: 特征重要性分析
# ============================================================
print("\n[Step 10] 特征重要性分析...")

print("\n  决策树特征重要性:")
dt_importances = dt_model.featureImportances
for i, imp in enumerate(dt_importances):
    feat_name = feature_cols[i] if i < len(feature_cols) else f'feature_{i}'
    print(f"    {feat_name}: {imp:.4f}")

print("\n  随机森林特征重要性:")
rf_importances = rf_model.featureImportances
for i, imp in enumerate(rf_importances):
    feat_name = feature_cols[i] if i < len(feature_cols) else f'feature_{i}'
    print(f"    {feat_name}: {imp:.4f}")

# ============================================================
# Step 11: 高风险参保人名单
# ============================================================
print("\n[Step 11] 高风险参保人名单...")

# 使用随机森林预测概率排序
high_risk = rf_predictions.filter(col("rf_prediction") == 1) \
    .orderBy(col("rf_prob").desc()) \
    .limit(20)

print("\n  高风险参保人TOP20:")
high_risk.select("person_id", "age_group", "insurance_type", "visit_count", "avg_visit_amount", "reimburse_rate", "is_abnormal", "rf_prob").show(20)

# ============================================================
# Step 12: 保存异常检测结果
# ============================================================
print("\n[Step 12] 保存异常检测结果...")

OUTPUT_DIR = "/home/hadoop/temp/analysis_results"
OUTPUT_PATH = f"file://{OUTPUT_DIR}/abnormal_results"

# 只保存随机森林结果（最优模型）
# rf_prob是向量类型，需要提取异常类概率（第二个元素）
from pyspark.sql.functions import udf
from pyspark.sql.types import DoubleType

# 定义UDF提取概率向量的第二个元素（异常类概率）
extract_prob_udf = udf(lambda v: float(v[1]) if v is not None and len(v) >= 2 else 0.0, DoubleType())

final_results = rf_predictions.select(
    "person_id", "age_group", "insurance_type", "visit_count", 
    "avg_visit_amount", "reimburse_rate", "total_amount",
    "is_abnormal", "rf_prediction", "rf_prob"
)

# 提取异常类概率（从向量中取第二个元素）
final_results = final_results.withColumn("abnormal_prob", extract_prob_udf(col("rf_prob")))

# 添加风险等级（使用提取的概率值）
final_results = final_results.withColumn(
    "risk_level",
    when(col("abnormal_prob") > 0.8, "高风险")
    .when(col("abnormal_prob") > 0.5, "中风险")
    .otherwise("低风险")
)

# 添加是否预测异常标签
final_results = final_results.withColumn(
    "predicted_abnormal",
    when(col("rf_prediction") == 1, "是").otherwise("否")
)

# 选择最终输出的列（去掉原始向量列）
final_results = final_results.select(
    "person_id", "age_group", "insurance_type", "visit_count", 
    "avg_visit_amount", "reimburse_rate", "total_amount",
    "is_abnormal", "rf_prediction", "abnormal_prob", "risk_level", "predicted_abnormal"
)

final_results.write.mode("overwrite").option("header", True).csv(OUTPUT_PATH)
print(f"  异常检测结果已保存: {OUTPUT_DIR}/abnormal_results")

# 显示保存结果样例
print("\n  保存结果样例:")
final_results.show(5)

# ============================================================
# Step 13: 清理资源
# ============================================================
print("\n[Step 13] 清理资源...")

spark.stop()
print("  SparkSession已关闭")

print("\n" + "=" * 60)
print("  医保异常行为识别完成")
print("=" * 60)