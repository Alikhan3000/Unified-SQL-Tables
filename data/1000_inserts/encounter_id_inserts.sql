-- add encounter_id, nullable
-- LAB RESULT
ALTER TABLE lab_result
ADD COLUMN encounter_id BIGINT UNSIGNED NULL;

UPDATE lab_result lr
JOIN ehr_encounter ee
  ON lr.patient_id = ee.patient_id
 AND lr.collection_time BETWEEN ee.encounter_start
                           AND COALESCE(ee.encounter_end, ee.encounter_start)
SET lr.encounter_id = ee.encounter_id;

-- connect encounter_id to the nearest encounter time
UPDATE lab_result lr
JOIN ehr_encounter ee
  ON ee.patient_id = lr.patient_id
 AND ee.encounter_start = (
     SELECT MAX(e2.encounter_start)
     FROM ehr_encounter e2
     WHERE e2.patient_id = lr.patient_id
       AND e2.encounter_start <= lr.collection_time
 )
SET lr.encounter_id = ee.encounter_id
WHERE lr.encounter_id IS NULL;

-- check valid encounter_id
SELECT
  COUNT(*) AS total_labs,
  SUM(encounter_id IS NOT NULL) AS labs_with_encounter,
  SUM(encounter_id IS NULL) AS labs_without_encounter
FROM lab_result;

-- check invalid encounter_id
SELECT COUNT(*) AS invalid_refs
FROM lab_result lr
LEFT JOIN ehr_encounter ee
  ON lr.encounter_id = ee.encounter_id
WHERE lr.encounter_id IS NOT NULL
  AND ee.encounter_id IS NULL;

-- add foreign key
ALTER TABLE lab_result
ADD CONSTRAINT fk_lab_encounter
FOREIGN KEY (encounter_id)
REFERENCES ehr_encounter(encounter_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- PROCEDURE RECORD
ALTER TABLE procedure_record
ADD COLUMN encounter_id BIGINT UNSIGNED NULL;

UPDATE procedure_record pr
JOIN ehr_encounter ee
  ON pr.patient_id = ee.patient_id
 AND pr.procedure_date BETWEEN ee.encounter_start
                           AND COALESCE(ee.encounter_end, ee.encounter_start)
SET pr.encounter_id = ee.encounter_id
WHERE pr.encounter_id IS NULL;

UPDATE procedure_record pr
JOIN ehr_encounter ee
  ON ee.patient_id = pr.patient_id
 AND ee.encounter_start = (
     SELECT MAX(e2.encounter_start)
     FROM ehr_encounter e2
     WHERE e2.patient_id = pr.patient_id
       AND e2.encounter_start <= pr.procedure_date
 )
SET pr.encounter_id = ee.encounter_id
WHERE pr.encounter_id IS NULL;

ALTER TABLE procedure_record
ADD CONSTRAINT fk_proc_encounter
FOREIGN KEY (encounter_id)
REFERENCES ehr_encounter(encounter_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- PHARMACY MEDICATION
ALTER TABLE pharmacy_medication
ADD COLUMN encounter_id BIGINT UNSIGNED NULL;

UPDATE pharmacy_medication pm
JOIN ehr_encounter ee
  ON pm.patient_id = ee.patient_id
 AND pm.fill_date BETWEEN DATE(ee.encounter_start)
                      AND DATE(COALESCE(ee.encounter_end, ee.encounter_start))
SET pm.encounter_id = ee.encounter_id
WHERE pm.encounter_id IS NULL;

UPDATE pharmacy_medication pm
JOIN ehr_encounter ee
  ON ee.patient_id = pm.patient_id
 AND ee.encounter_start = (
     SELECT MAX(e2.encounter_start)
     FROM ehr_encounter e2
     WHERE e2.patient_id = pm.patient_id
       AND DATE(e2.encounter_start) <= pm.fill_date
 )
SET pm.encounter_id = ee.encounter_id
WHERE pm.encounter_id IS NULL;

ALTER TABLE pharmacy_medication
ADD CONSTRAINT fk_med_encounter
FOREIGN KEY (encounter_id)
REFERENCES ehr_encounter(encounter_id)
ON DELETE SET NULL
ON UPDATE CASCADE;