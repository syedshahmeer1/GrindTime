PRAGMA foreign_keys = ON;

-- User and profile
CREATE TABLE IF NOT EXISTS users 
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_profiles 
(
    user_id          INTEGER NOT NULL UNIQUE
                     REFERENCES users(id) ON DELETE CASCADE,
    display_name     TEXT,
    sex              TEXT CHECK (sex IN ('male','female','other')),
    dob              TEXT,          -- 'YYYY-MM-DD'
    height_cm        REAL CHECK (height_cm IS NULL OR height_cm >= 0),
    weight_kg        REAL CHECK (weight_kg IS NULL OR weight_kg >= 0),
    activity_factor  REAL CHECK (activity_factor IS NULL OR activity_factor >= 0),
    experience_level TEXT
);

-- logging workout
CREATE TABLE IF NOT EXISTS workout_sessions 
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL
               REFERENCES users(id) ON DELETE CASCADE,
    started_at TEXT,
    ended_at   TEXT,
    notes      TEXT
);

CREATE TABLE IF NOT EXISTS workout_sets 
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id    INTEGER NOT NULL
                  REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    set_index     INTEGER NOT NULL CHECK (set_index >= 0),
    reps          INTEGER NOT NULL CHECK (reps >= 0),
    weight_kg     REAL NOT NULL CHECK (weight_kg >= 0),
    rpe           REAL CHECK (rpe IS NULL OR (rpe >= 1.0 AND rpe <= 10.0)),
    rest_seconds  INTEGER CHECK (rest_seconds IS NULL OR rest_seconds >= 0),
    is_warmup     INTEGER NOT NULL DEFAULT 0 CHECK (is_warmup IN (0,1))
);


-- Progress track
CREATE TABLE IF NOT EXISTS body_metrics 
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL
                REFERENCES users(id) ON DELETE CASCADE,
    measured_at TEXT NOT NULL,  
    weight_kg   REAL CHECK (weight_kg IS NULL OR weight_kg >= 0),
    bodyfat_pct REAL CHECK (bodyfat_pct IS NULL OR (bodyfat_pct >= 0 AND bodyfat_pct <= 100)),
    chest_cm    REAL CHECK (chest_cm IS NULL OR chest_cm >= 0),
    waist_cm    REAL CHECK (waist_cm IS NULL OR waist_cm >= 0),
    hips_cm     REAL CHECK (hips_cm IS NULL OR hips_cm >= 0),
    UNIQUE (user_id, measured_at)
);

CREATE TABLE IF NOT EXISTS exercise_prs 
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL
                  REFERENCES users(id) ON DELETE CASCADE,
    exercise_name TEXT NOT NULL,
    pr_type       TEXT NOT NULL CHECK (pr_type IN ('1RM','3RM','Volume')),
    value         REAL NOT NULL CHECK (value >= 0),
    achieved_at   TEXT NOT NULL,
    notes         TEXT,
    UNIQUE (user_id, exercise_name, pr_type, achieved_at)
);


-- Nutrtition
CREATE TABLE IF NOT EXISTS nutrition_entries 
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL
                 REFERENCES users(id) ON DELETE CASCADE,
    eaten_at     TEXT NOT NULL,
    fdc_id       INTEGER,
    serving_qty  REAL CHECK (serving_qty IS NULL OR serving_qty >= 0),
    serving_unit TEXT,
    calories     REAL CHECK (calories IS NULL OR calories >= 0),
    protein_g    REAL CHECK (protein_g IS NULL OR protein_g >= 0),
    carbs_g      REAL CHECK (carbs_g IS NULL OR carbs_g >= 0),
    fat_g        REAL CHECK (fat_g IS NULL OR fat_g >= 0),
    notes        TEXT
);

CREATE TABLE IF NOT EXISTS macro_targets 
(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL
                  REFERENCES users(id) ON DELETE CASCADE,
    effective_from TEXT NOT NULL,  
    goal          TEXT NOT NULL CHECK (goal IN ('bulk','cut','maintain')),
    kcal          INTEGER NOT NULL CHECK (kcal >= 0),
    protein_g     INTEGER NOT NULL CHECK (protein_g >= 0),
    carbs_g       INTEGER NOT NULL CHECK (carbs_g >= 0),
    fat_g         INTEGER NOT NULL CHECK (fat_g >= 0),
    UNIQUE (user_id, effective_from)
);

-- Calorie calculator saved results (latest can be shown on profile)
CREATE TABLE IF NOT EXISTS calorie_calc_results
(
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL
                        REFERENCES users(id) ON DELETE CASCADE,
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),

    height_ft           INTEGER CHECK (height_ft IS NULL OR height_ft >= 0),
    height_in           INTEGER CHECK (height_in IS NULL OR (height_in >= 0 AND height_in < 12)),
    weight_kg           REAL    CHECK (weight_kg IS NULL OR weight_kg >= 0),
    age_years           INTEGER CHECK (age_years IS NULL OR age_years >= 0),
    sex                 TEXT    CHECK (sex IN ('male','female','other')),
    activity_factor     REAL    CHECK (activity_factor IS NULL OR activity_factor >= 0),
    experience_level    TEXT,

    bmr_kcal            INTEGER CHECK (bmr_kcal IS NULL OR bmr_kcal >= 0),
    maintenance_kcal    INTEGER CHECK (maintenance_kcal IS NULL OR maintenance_kcal >= 0),
    bulk_kcal           INTEGER CHECK (bulk_kcal IS NULL OR bulk_kcal >= 0),
    cut_kcal            INTEGER CHECK (cut_kcal IS NULL OR cut_kcal >= 0),
    aggressive_cut_kcal INTEGER CHECK (aggressive_cut_kcal IS NULL OR aggressive_cut_kcal >= 0),
    protein_low_g       INTEGER CHECK (protein_low_g IS NULL OR protein_low_g >= 0),
    protein_high_g      INTEGER CHECK (protein_high_g IS NULL OR protein_high_g >= 0)
);

CREATE INDEX IF NOT EXISTS idx_calorie_calc_results_user_created
ON calorie_calc_results (user_id, created_at DESC);