-- Explorer Scraper Database Schema
-- PostgreSQL 14+

-- Drop existing tables (for clean setup)
DROP TABLE IF EXISTS used_deals CASCADE;
DROP TABLE IF EXISTS deals CASCADE;
DROP TABLE IF EXISTS raw_explore_cards CASCADE;
DROP TABLE IF EXISTS origins CASCADE;

-- ============================================================================
-- Origins table (airports we scrape)
-- ============================================================================

CREATE TABLE origins (
    id SERIAL PRIMARY KEY,
    iata_code VARCHAR(3) NOT NULL UNIQUE,
    airport_name VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    country VARCHAR(2) DEFAULT 'US',
    tier INTEGER DEFAULT 2,  -- 1 = high priority, 2 = normal
    status VARCHAR(20) DEFAULT 'active',  -- active, paused, disabled
    timezone VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scraped_at TIMESTAMP,
    
    -- Stats
    total_deals_found INTEGER DEFAULT 0,
    total_deals_published INTEGER DEFAULT 0
);

CREATE INDEX idx_origins_iata ON origins(iata_code);
CREATE INDEX idx_origins_status ON origins(status);
CREATE INDEX idx_origins_tier ON origins(tier);

-- ============================================================================
-- Raw explore cards (audit trail of all scraped cards)
-- ============================================================================

CREATE TABLE raw_explore_cards (
    id SERIAL PRIMARY KEY,
    origin_iata VARCHAR(3) NOT NULL,
    destination_name VARCHAR(255) NOT NULL,
    search_region VARCHAR(50) NOT NULL,  -- europe, caribbean, etc.
    
    -- Price & dates
    min_price INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    start_date DATE,
    end_date DATE,
    duration VARCHAR(50),
    
    -- Metadata
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scrape_run_id UUID  -- group cards from same scrape run
);

CREATE INDEX idx_explore_cards_origin ON raw_explore_cards(origin_iata);
CREATE INDEX idx_explore_cards_region ON raw_explore_cards(search_region);
CREATE INDEX idx_explore_cards_scraped ON raw_explore_cards(scraped_at);

-- ============================================================================
-- Deals table (canonical valid deals after expansion + filtering)
-- ============================================================================

CREATE TABLE deals (
    id SERIAL PRIMARY KEY,
    deal_id VARCHAR(100) NOT NULL UNIQUE,  -- phx-dub-20260201
    
    -- Origin
    origin_iata VARCHAR(3) NOT NULL,
    origin_airport_name VARCHAR(255),
    
    -- Destination
    destination_airport VARCHAR(3) NOT NULL,
    destination_city VARCHAR(255) NOT NULL,
    destination_country VARCHAR(2) NOT NULL,
    destination_region VARCHAR(50) NOT NULL,  -- europe, caribbean, etc.
    
    -- Pricing
    reference_price INTEGER NOT NULL,
    usual_price_estimate INTEGER,
    discount_amount INTEGER,
    discount_pct DECIMAL(5, 4),  -- 0.2895 = 28.95%
    
    -- Flexibility
    similar_dates_count INTEGER NOT NULL,
    first_travel_date DATE NOT NULL,
    last_travel_date DATE NOT NULL,
    
    -- Display
    deal_quality_text VARCHAR(255),  -- "$388 cheaper than usual"
    
    -- Flight details (JSON blob)
    flight_details JSONB,  -- {airline, duration, stops, departure_time, arrival_time}
    
    -- Metadata
    search_region VARCHAR(50),  -- which Explore region found it
    source VARCHAR(50) DEFAULT 'google_flights_price_graph',
    
    -- Deal evaluation
    is_valid_deal BOOLEAN DEFAULT TRUE,
    is_featured_candidate BOOLEAN DEFAULT FALSE,
    score DECIMAL(5, 4) NOT NULL,  -- 0.0–1.0
    
    -- Timestamps
    expanded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    threshold_used DECIMAL(3, 2) DEFAULT 0.10,
    
    -- Similar deals data (JSON blob - full list of date/price combos)
    similar_deals JSONB  -- [{"start_date": "2026-02-01", "end_date": "2026-02-08", "price": 433}, ...]
);

CREATE INDEX idx_deals_deal_id ON deals(deal_id);
CREATE INDEX idx_deals_origin ON deals(origin_iata);
CREATE INDEX idx_deals_destination ON deals(destination_airport);
CREATE INDEX idx_deals_region ON deals(destination_region);
CREATE INDEX idx_deals_discount ON deals(discount_pct DESC);
CREATE INDEX idx_deals_score ON deals(score DESC);
CREATE INDEX idx_deals_travel_dates ON deals(first_travel_date, last_travel_date);
CREATE INDEX idx_deals_expanded ON deals(expanded_at);
CREATE INDEX idx_deals_featured ON deals(is_featured_candidate) WHERE is_featured_candidate = TRUE;

-- Composite index for common queries
CREATE INDEX idx_deals_origin_region_score ON deals(origin_iata, destination_region, score DESC);

-- ============================================================================
-- Used deals table (track what we've already published)
-- ============================================================================

CREATE TABLE used_deals (
    id SERIAL PRIMARY KEY,
    deal_id VARCHAR(100) NOT NULL,
    
    -- Origin/destination for quick lookups
    origin_iata VARCHAR(3) NOT NULL,
    destination_airport VARCHAR(3) NOT NULL,
    destination_region VARCHAR(50),
    
    -- When & where published
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_in VARCHAR(50),  -- email, blog, social, etc.
    
    -- Date window (to avoid republishing similar date ranges)
    first_travel_date DATE,
    last_travel_date DATE,
    
    -- Reference back to original deal
    deal_table_id INTEGER REFERENCES deals(id) ON DELETE SET NULL,
    
    -- Expiry (auto-cleanup after 35 days)
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '35 days')
);

CREATE INDEX idx_used_deals_origin ON used_deals(origin_iata);
CREATE INDEX idx_used_deals_destination ON used_deals(destination_airport);
CREATE INDEX idx_used_deals_expires ON used_deals(expires_at);
CREATE INDEX idx_used_deals_published ON used_deals(published_at);

-- Composite index for "is this deal recently used?" queries
CREATE INDEX idx_used_deals_origin_dest ON used_deals(origin_iata, destination_airport, expires_at);

-- ============================================================================
-- Helper functions & triggers
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = CURRENT_TIMESTAMP;
   RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_origins_updated_at BEFORE UPDATE ON origins
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Sample data (optional - for testing)
-- ============================================================================

-- Add a few origins for testing
INSERT INTO origins (iata_code, airport_name, city, state, tier) VALUES
('PHX', 'Phoenix Sky Harbor International Airport', 'Phoenix', 'AZ', 1),
('DFW', 'Dallas/Fort Worth International Airport', 'Dallas', 'TX', 1),
('LAX', 'Los Angeles International Airport', 'Los Angeles', 'CA', 1),
('JFK', 'John F. Kennedy International Airport', 'New York', 'NY', 1),
('ORD', 'O''Hare International Airport', 'Chicago', 'IL', 1)
ON CONFLICT (iata_code) DO NOTHING;

-- ============================================================================
-- Views for common queries
-- ============================================================================

-- Active valid deals (not recently used)
CREATE OR REPLACE VIEW active_deals AS
SELECT 
    d.*,
    CASE 
        WHEN ud.id IS NOT NULL THEN TRUE 
        ELSE FALSE 
    END as recently_used
FROM deals d
LEFT JOIN used_deals ud ON 
    d.origin_iata = ud.origin_iata 
    AND d.destination_airport = ud.destination_airport
    AND ud.expires_at > CURRENT_TIMESTAMP
    AND (
        -- Check if date ranges overlap
        (d.first_travel_date, d.last_travel_date) OVERLAPS (ud.first_travel_date, ud.last_travel_date)
    )
WHERE d.is_valid_deal = TRUE;

-- Featured deals by origin (top deals, not recently used)
CREATE OR REPLACE VIEW featured_deals_by_origin AS
SELECT 
    origin_iata,
    destination_region,
    COUNT(*) as deal_count,
    AVG(discount_pct) as avg_discount,
    AVG(score) as avg_score
FROM active_deals
WHERE is_featured_candidate = TRUE
  AND recently_used = FALSE
GROUP BY origin_iata, destination_region
ORDER BY origin_iata, avg_score DESC;

-- ============================================================================
-- Cleanup job (run daily via cron)
-- ============================================================================

-- Delete expired used_deals entries
-- Run: DELETE FROM used_deals WHERE expires_at < CURRENT_TIMESTAMP;

COMMENT ON DATABASE CURRENT_DATABASE IS 'Explorer Scraper - Flight deals database';
COMMENT ON TABLE origins IS 'Airports we scrape deals from';
COMMENT ON TABLE raw_explore_cards IS 'Audit trail of all raw Explore cards scraped';
COMMENT ON TABLE deals IS 'Canonical valid deals after expansion and filtering';
COMMENT ON TABLE used_deals IS 'Track published deals to avoid repeats (35-day window)';

