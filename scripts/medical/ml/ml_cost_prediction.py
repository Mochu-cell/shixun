#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医疗费用预测模型（Spark MLlib）
使用Spark MLlib实现线性回归和随机森林回归

运行方式：
  spark-submit ml_cost_prediction.py

数据格式说明：
  dm_insurance_stats.csv 使用 | 分隔符，无列名
  列顺序：person_id|age_group|insurance_type|visit_count|total_amount|reimburse_amount|reimburse_rate|avg_visit_amount|first_visit_date|last_visit_date|etl_date
"""

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.regression import LinearRegression, RandomForestRegressor
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col, when, lit
import os

print("=" * 60)
print("  医疗费用预测模型（Spark MLlib）")
print("=" * 60)

# ============================================================
# Step 1: 创建SparkSession
# ============================================================
print("\n[Step 1] 创建SparkSession...")

spark = SparkSession.builder \
    .appName("CostPrediction") \
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
        'visit_count': np.random.randint(1, 15, n_samples),
        'avg_visit_amount': np.random.uniform(500, 5000, n_samples),
        'reimburse_rate': np.random.uniform(0.3, 0.9, n_samples),
        'enroll_months': np.random.randint(6, 120, n_samples)
    })
    
    mock_data['total_amount'] = mock_data['visit_count'] * mock_data['avg_visit_amount']
    
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
# Step 3: 数据预处理
# ============================================================
print("\n[Step 3] 数据预处理...")

# 检查是否有 enroll_months 列（如果没有，用日期计算）
if 'enroll_months' not in df.columns:
    print("  [构造] 计算 enroll_months...")
    # 简化处理，假设参保时间为 12 个月
    df = df.withColumn('enroll_months', lit(12))

# 清洗数据：处理负值和异常值
df = df.filter(col('total_amount') > 0)  # 过滤负值
df = df.filter(col('avg_visit_amount') > 0)

print(f"  有效数据: {df.count()}条")

# ============================================================
# Step 4: 特征构造Pipeline
# ============================================================
print("\n[Step 4] 构建特征Pipeline...")

# StringIndexer - 将字符串特征转换为数值
age_indexer = StringIndexer(inputCol="age_group", outputCol="age_encoded", handleInvalid="keep")
insurance_indexer = StringIndexer(inputCol="insurance_type", outputCol="insurance_encoded", handleInvalid="keep")

# VectorAssembler - 合并特征向量
feature_cols = ["age_encoded", "insurance_encoded", "enroll_months", "visit_count", "avg_visit_amount", "reimburse_rate"]
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")

# StandardScaler - 特征标准化
scaler = StandardScaler(inputCol="features", outputCol="scaled_features", withStd=True, withMean=False)

# Pipeline
preprocess_pipeline = Pipeline(stages=[age_indexer, insurance_indexer, assembler, scaler])
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
# Step 6: 线性回归模型
# ============================================================
print("\n[Step 6] 线性回归模型训练...")

lr = LinearRegression(
    featuresCol="scaled_features",
    labelCol="total_amount",
    predictionCol="lr_prediction",
    maxIter=100,
    regParam=0.1,
    elasticNetParam=0.5
)

lr_model = lr.fit(train_data)
lr_predictions = lr_model.transform(test_data)

print("  线性回归模型训练完成")

# 输出系数
print("\n  线性回归系数:")
print(f"    截距: {lr_model.intercept:.2f}")
print(f"    特征系数: {lr_model.coefficients}")

# ============================================================
# Step 7: 随机森林回归模型
# ============================================================
print("\n[Step 7] 随机森林回归模型训练...")

rf = RandomForestRegressor(
    featuresCol="scaled_features",
    labelCol="total_amount",
    predictionCol="rf_prediction",
    numTrees=50,
    maxDepth=8,
    seed=42
)

rf_model = rf.fit(train_data)
rf_predictions = rf_model.transform(test_data)

print("  随机森林模型训练完成")

# 特征重要性
print("\n  随机森林特征重要性:")
rf_importances = rf_model.featureImportances
for i, imp in enumerate(rf_importances):
    feat_name = feature_cols[i] if i < len(feature_cols) else f'feature_{i}'
    print(f"    {feat_name}: {imp:.4f}")

# ============================================================
# Step 8: 模型评估对比
# ============================================================
print("\n[Step 8] 模型评估对比...")

# RMSE评估器
rmse_evaluator = RegressionEvaluator(labelCol="total_amount", predictionCol="lr_prediction", metricName="rmse")
# MAE评估器
mae_evaluator = RegressionEvaluator(labelCol="total_amount", predictionCol="lr_prediction", metricName="mae")
# R2评估器
r2_evaluator = RegressionEvaluator(labelCol="total_amount", predictionCol="lr_prediction", metricName="r2")

# 线性回归评估
lr_rmse = rmse_evaluator.evaluate(lr_predictions)
lr_mae = mae_evaluator.evaluate(lr_predictions)
lr_r2 = r2_evaluator.evaluate(lr_predictions)

# 随机森林评估
rmse_evaluator.setPredictionCol("rf_prediction")
rf_rmse = rmse_evaluator.evaluate(rf_predictions)
mae_evaluator.setPredictionCol("rf_prediction")
rf_mae = mae_evaluator.evaluate(rf_predictions)
r2_evaluator.setPredictionCol("rf_prediction")
rf_r2 = r2_evaluator.evaluate(rf_predictions)

print("\n" + "=" * 60)
print("  模型对比结果")
print("=" * 60)
print(f"\n  {'模型':<12} {'RMSE':<15} {'MAE':<15} {'R²':<10}")
print(f"  {'线性回归':<12} {lr_rmse:<15.2f} {lr_mae:<15.2f} {lr_r2:<10.4f}")
print(f"  {'随机森林':<12} {rf_rmse:<15.2f} {rf_mae:<15.2f} {rf_r2:<10.4f}")

# ============================================================
# Step 9: 预测结果展示
# ============================================================
print("\n[Step 9] 预测结果展示...")

print("\n  线性回归预测样例:")
lr_predictions.select("person_id", "age_group", "insurance_type", "visit_count", "total_amount", "lr_prediction") \
    .show(10)

print("\n  随机森林预测样例:")
rf_predictions.select("person_id", "age_group", "insurance_type", "visit_count", "total_amount", "rf_prediction") \
    .show(10)

# ============================================================
# Step 10: 保存预测模型
# ============================================================
print("\n[Step 10] 保存预测结果...")

OUTPUT_DIR = "/home/hadoop/temp/analysis_results"
OUTPUT_PATH = f"file://{OUTPUT_DIR}/prediction_results"

# 合并预测结果
final_results = lr_predictions.select(
    "person_id", "age_group", "insurance_type", "visit_count", "avg_visit_amount",
    "total_amount", "lr_prediction", "rf_prediction"
)

# 添加预测误差
final_results = final_results.withColumn(
    "lr_error", col("total_amount") - col("lr_prediction")
).withColumn(
    "rf_error", col("total_amount") - col("rf_prediction")
)

# 添加预测准确度评估
final_results = final_results.withColumn(
    "best_model",
    when(abs(col("lr_error")) < abs(col("rf_error")), "线性回归")
    .otherwise("随机森林")
)

final_results.write.mode("overwrite").option("header", True).csv(OUTPUT_PATH)
print(f"  预测结果已保存: {OUTPUT_DIR}/prediction_results")

# ============================================================
# Step 11: 清理资源
# ============================================================
print("\n[Step 11] 清理资源...")

spark.stop()
print("  SparkSession已关闭")

print("\n" + "=" * 60)
print("  医疗费用预测模型构建完成")
print("=" * 60)