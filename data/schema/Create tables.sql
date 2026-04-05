use unified;
CREATE TABLE patient_demographics (
patient_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
COMMENT 'Surrogate key that uniquely identifies a patient in your platform; used as the main foreign key in other tables.',

external_patient_id VARCHAR(64)
COMMENT 'Optional source-system identifier (e.g., MRN) for trace-back to the originating EHR or registration system.',

first_name VARCHAR(100)
COMMENT 'Patient first name (can be excluded or tokenized in de-identified views).',

last_name VARCHAR(100)
COMMENT 'Patient last name (can be excluded or tokenized in de-identified views).',

date_of_birth DATE NOT NULL
COMMENT 'Full date of birth; can be truncated to year for privacy in analytics views.',

sex_at_birth VARCHAR(50) NOT NULL
COMMENT 'Sex assigned at birth (Male, Female, Intersex, Unknown, etc.).',

gender_identity VARCHAR(50)
COMMENT 'Current gender identity, kept separate from sex_at_birth.',

race VARCHAR(50)
COMMENT 'High-level race category; could later be normalized to coded vocabularies.',

ethnicity VARCHAR(50)
COMMENT 'Ethnicity such as Hispanic/Latino, Not Hispanic/Latino, Unknown, etc.',

preferred_language VARCHAR(50)
COMMENT 'Primary language for communication, used for care coordination.',

country VARCHAR(100)
COMMENT 'Country of residence.',

state_province VARCHAR(100)
COMMENT 'State or province; useful for regional analytics and area-level indices.',

city VARCHAR(100)
COMMENT 'City of residence.',

postal_code VARCHAR(20)
COMMENT 'Zip/postal code, often used to link to neighborhood-level indicators.',

created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
COMMENT 'Timestamp when the record was first created in the unified platform.',

updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT 'Last time this demographic record was updated.'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =========================================================
-- 2) Socioeconomic information (SDOH) per patient
-- =========================================================

use unified;
CREATE TABLE patient_socioeconomic (
soc_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
COMMENT 'Surrogate key for this socioeconomic record; allows multiple time-stamped rows per patient.',

patient_id BIGINT UNSIGNED NOT NULL
COMMENT 'Foreign key to patient_demographics.patient_id.',

effective_start_date DATE NOT NULL
COMMENT 'Date when this set of socioeconomic attributes became valid.',

effective_end_date DATE
COMMENT 'Optional end date; NULL means the record is current.',

employment_status VARCHAR(50)
COMMENT 'Employment status (full-time, part-time, unemployed, student, retired, etc.).',

income_bracket VARCHAR(50)
COMMENT 'Income band for privacy (e.g., <25k, 25k-50k, etc.).',

education_level VARCHAR(100)
COMMENT 'Highest level of education completed.',

housing_status VARCHAR(100)
COMMENT 'Housing situation (stable, renting, homeless, shelter, at risk, unknown).',

household_size INT
COMMENT 'Number of people living in the same household.',

marital_status VARCHAR(50)
COMMENT 'Single, Married, Divorced, Widowed, Domestic partnership, etc.',

insurance_type VARCHAR(100)
COMMENT 'Primary payer category (Commercial, Medicare, Medicaid, Self-pay, etc.).',

food_insecurity_flag BOOLEAN
COMMENT 'TRUE if patient is documented as food insecure.',

transportation_barrier_flag BOOLEAN
COMMENT 'TRUE if patient reports transport barriers to accessing care.',

notes TEXT
COMMENT 'Optional short summary of SDOH screening results or context (avoid PHI).',

created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
COMMENT 'When this socioeconomic record was first created.',

updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT 'Last time this record was updated.',

CONSTRAINT fk_socio_patient
FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
ON UPDATE CASCADE ON DELETE CASCADE
);


-- =========================================================
-- 3) Remote device data (wearables / home monitoring)
-- =========================================================
CREATE TABLE remote_device_reading (
device_reading_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
COMMENT 'Surrogate key for each individual device reading.',

patient_id BIGINT UNSIGNED NOT NULL
COMMENT 'Foreign key to patient_demographics.patient_id; links readings to a patient.',

device_id VARCHAR(100) NOT NULL
COMMENT 'Logical identifier for the device in your platform.',

device_type VARCHAR(100) NOT NULL
COMMENT 'General category (Smartwatch, Glucometer, BP cuff, Pulse oximeter, etc.).',

manufacturer VARCHAR(100)
COMMENT 'Device manufacturer (Apple, Fitbit, Omron, etc.).',

model VARCHAR(100)
COMMENT 'Device model name/number (e.g., Apple Watch Series 9).',

measurement_type VARCHAR(100) NOT NULL
COMMENT 'What was measured (heart_rate, steps, systolic_bp, spo2, glucose, etc.).',

measurement_value DECIMAL(18,4) NOT NULL
COMMENT 'Numeric value of the measurement (precision can be tuned).',

measurement_unit VARCHAR(50)
COMMENT 'Unit of measure (bpm, mmHg, mg/dL, kg, %, steps, etc.).',

measurement_time DATETIME NOT NULL
COMMENT 'Timestamp (preferably UTC) when the device recorded the measurement.',

ingestion_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
COMMENT 'When your platform received the reading.',

data_quality_flag VARCHAR(50)
COMMENT 'Simple QA flag: OK, ESTIMATED, OUT_OF_RANGE, ARTIFACT, etc.',

source_system VARCHAR(100)
COMMENT 'Origin system (Apple HealthKit, Google Fit, Vendor API X, etc.).',

context_encounter_id VARCHAR(64)
COMMENT 'Optional ID for the encounter/telehealth session associated with this reading.',

raw_payload JSON
COMMENT 'Optional raw JSON payload from the vendor/device for traceability.',

created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
COMMENT 'When this row was created in the DB.',

updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
COMMENT 'Last time this record was updated.',

CONSTRAINT fk_device_patient
FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
ON UPDATE CASCADE ON DELETE CASCADE
);


select * from remote_device_reading;


use unified;
CREATE TABLE ehr_encounter (
    encounter_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
        COMMENT 'Unique identifier for each clinical encounter.',

    patient_id BIGINT UNSIGNED NOT NULL
        COMMENT 'FK to patient_demographics.patient_id.',

    encounter_type VARCHAR(100) NOT NULL
        COMMENT 'Inpatient, Outpatient, ED, Telehealth, Urgent Care, etc.',

    encounter_start DATETIME NOT NULL
        COMMENT 'Start time of the encounter.',

    encounter_end DATETIME
        COMMENT 'End time of the encounter; NULL if ongoing.',

    provider_id VARCHAR(64)
        COMMENT 'Optional provider identifier from EHR.',

    facility VARCHAR(200)
        COMMENT 'Hospital or clinic where encounter occurred.',

    chief_complaint VARCHAR(255)
        COMMENT 'Primary reason for visit.',

    notes TEXT
        COMMENT 'Optional clinical notes (avoid PHI in analytics).',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ehr_patient
        FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);


use unified;

CREATE TABLE claims_encounter (
    claim_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
        COMMENT 'Unique identifier for each claim record.',

    patient_id BIGINT UNSIGNED NOT NULL
        COMMENT 'FK to patient_demographics.patient_id.',

    claim_number VARCHAR(100) NOT NULL
        COMMENT 'Payer claim number.',

    payer VARCHAR(200)
        COMMENT 'Insurance payer name.',

    claim_status VARCHAR(50)
        COMMENT 'Submitted, Paid, Denied, Pending, etc.',

    service_start_date DATE NOT NULL
        COMMENT 'Start of service period.',

    service_end_date DATE
        COMMENT 'End of service period.',

    billed_amount DECIMAL(18,2)
        COMMENT 'Total amount billed.',

    paid_amount DECIMAL(18,2)
        COMMENT 'Amount paid by payer.',

    diagnosis_codes JSON
        COMMENT 'List of ICD-10 codes associated with the claim.',

    procedure_codes JSON
        COMMENT 'List of CPT/HCPCS codes associated with the claim.',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_claims_patient
        FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);
use unified;

CREATE TABLE lab_result (
    lab_result_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
        COMMENT 'Unique identifier for each lab result.',

    patient_id BIGINT UNSIGNED NOT NULL
        COMMENT 'FK to patient_demographics.patient_id.',

    test_code VARCHAR(50) NOT NULL
        COMMENT 'LOINC or internal test code.',

    test_name VARCHAR(200) NOT NULL
        COMMENT 'Human-readable test name.',

    result_value VARCHAR(100)
        COMMENT 'Raw result value (string to support non-numeric results).',

    result_numeric DECIMAL(18,4)
        COMMENT 'Numeric result when applicable.',

    unit VARCHAR(50)
        COMMENT 'Unit of measure.',

    reference_range VARCHAR(100)
        COMMENT 'Normal range for interpretation.',

    abnormal_flag VARCHAR(20)
        COMMENT 'High, Low, Normal, Critical, etc.',

    collection_time DATETIME
        COMMENT 'When specimen was collected.',

    result_time DATETIME
        COMMENT 'When result was finalized.',

    performing_lab VARCHAR(200)
        COMMENT 'Lab or facility performing the test.',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lab_patient
        FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);


use unified;

CREATE TABLE pharmacy_medication (
    medication_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
        COMMENT 'Unique identifier for each medication record.',

    patient_id BIGINT UNSIGNED NOT NULL
        COMMENT 'FK to patient_demographics.patient_id.',

    medication_name VARCHAR(200) NOT NULL
        COMMENT 'Drug name (generic or brand).',

    ndc_code VARCHAR(20)
        COMMENT 'National Drug Code if available.',

    dosage VARCHAR(100)
        COMMENT 'Dosage instructions (e.g., 10 mg).',

    route VARCHAR(50)
        COMMENT 'Oral, IV, IM, Subcutaneous, etc.',

    frequency VARCHAR(50)
        COMMENT 'How often the medication is taken.',

    quantity INT
        COMMENT 'Quantity dispensed.',

    days_supply INT
        COMMENT 'Number of days the medication should last.',

    prescribing_provider VARCHAR(100)
        COMMENT 'Provider who prescribed the medication.',

    fill_date DATE
        COMMENT 'Date the prescription was filled.',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_med_patient
        FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);

select * from pharmacy_medication;

use unified;
CREATE TABLE procedure_record (
    procedure_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY
        COMMENT 'Unique identifier for each procedure.',

    patient_id BIGINT UNSIGNED NOT NULL
        COMMENT 'FK to patient_demographics.patient_id.',

    procedure_code VARCHAR(50) NOT NULL
        COMMENT 'CPT/HCPCS or internal procedure code.',

    procedure_description VARCHAR(255)
        COMMENT 'Human-readable description of the procedure.',

    procedure_date DATETIME NOT NULL
        COMMENT 'When the procedure was performed.',

    performing_provider VARCHAR(100)
        COMMENT 'Provider who performed the procedure.',

    facility VARCHAR(200)
        COMMENT 'Location where procedure occurred.',

    anesthesia_type VARCHAR(100)
        COMMENT 'General, Local, Regional, None.',

    notes TEXT
        COMMENT 'Optional notes (avoid PHI).',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_proc_patient
        FOREIGN KEY (patient_id) REFERENCES patient_demographics(patient_id)
        ON UPDATE CASCADE ON DELETE CASCADE
);


select * from ehr_encounter;
select * from procedure_record;
select * from pharmacy_medication;
select * from lab_result;
select * from claims_encounter;
