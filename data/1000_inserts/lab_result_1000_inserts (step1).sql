
USE unified;
SELECT DATABASE();

-- creat temp lab_result_stage with 13 columns to load the 13 columns

CREATE TEMPORARY TABLE lab_result_stage (
  patient_id BIGINT,
  test_code VARCHAR(50),
  test_name VARCHAR(200),
  result_value VARCHAR(100),
  result_numeric DECIMAL(18,4),
  unit VARCHAR(50),
  reference_range VARCHAR(100),
  abnormal_flag VARCHAR(20),
  collection_time DATETIME,
  result_time DATETIME,
  performing_lab VARCHAR(200),
  created_at DATETIME,
  updated_at DATETIME
);