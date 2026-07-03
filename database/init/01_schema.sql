-- MosquiSense AI — PostgreSQL + PostGIS initialization
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Water classification enum
DO $$ BEGIN
    CREATE TYPE water_class AS ENUM (
        'no_water', 'moving', 'temporary', 'stagnant', 'flooded'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE user_role AS ENUM (
        'super_admin', 'state_admin', 'municipal_officer',
        'field_operator', 'analyst', 'citizen'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Core geography (simplified MVP — full schema in Alembic migrations)
CREATE TABLE IF NOT EXISTS states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lgd_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    geom GEOMETRY(MultiPolygon, 4326)
);

CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_id UUID REFERENCES states(id),
    lgd_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS wards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID REFERENCES districts(id),
    ward_code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    population INTEGER DEFAULT 0,
    drain_density FLOAT DEFAULT 0,
    centroid GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ward_boundaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward_id UUID REFERENCES wards(id) ON DELETE CASCADE,
    geom GEOMETRY(MultiPolygon, 4326) NOT NULL,
    effective_from DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_ward_boundaries_geom ON ward_boundaries USING GIST (geom);

CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward_id UUID REFERENCES wards(id),
    predicted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    risk_score FLOAT CHECK (risk_score >= 0 AND risk_score <= 100),
    outbreak_probability FLOAT CHECK (outbreak_probability >= 0 AND outbreak_probability <= 1),
    horizon_15d JSONB,
    model_version VARCHAR(50)
);

SELECT create_hypertable('predictions', 'predicted_at', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_predictions_ward_time ON predictions (ward_id, predicted_at DESC);

-- Seed Uttar Pradesh + Lucknow placeholder
INSERT INTO states (lgd_code, name) VALUES ('09', 'Uttar Pradesh')
ON CONFLICT (lgd_code) DO NOTHING;
