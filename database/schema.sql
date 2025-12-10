-- Flight Deals Database Schema
-- PostgreSQL 15+

-- Primary table: expanded_deals
-- Stores ALL flexible date combinations for each deal
-- NO UNIQUE constraint - allows duplicate deals to track history
CREATE TABLE IF NOT EXISTS expanded_deals (
    id SERIAL PRIMARY KEY,
    
    -- Core flight info
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    destination_city VARCHAR(100),  -- City name (e.g., "London")
    outbound_date DATE NOT NULL,
    return_date DATE NOT NULL,
    price INTEGER NOT NULL,
    
    -- Original deal context (from explore phase)
    reference_price INTEGER NOT NULL,  -- The explore card price
    search_region VARCHAR(50),  -- e.g., "europe", "asia", "caribbean"
    duration VARCHAR(50),  -- e.g., "8 hours 30 minutes"
    
    -- Expansion context
    similar_date_count INTEGER NOT NULL,  -- Total similar dates found for this deal
    
    -- Clickable URL
    google_flights_url TEXT,  -- Direct link to this specific flight
    
    -- Tracking
    found_at TIMESTAMP DEFAULT NOW(),
    posted BOOLEAN DEFAULT FALSE,
    posted_at TIMESTAMP NULL
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_origin_dest ON expanded_deals(origin, destination);
CREATE INDEX IF NOT EXISTS idx_found_at ON expanded_deals(found_at);
CREATE INDEX IF NOT EXISTS idx_posted ON expanded_deals(posted);
CREATE INDEX IF NOT EXISTS idx_route_recency ON expanded_deals(origin, destination, found_at);
CREATE INDEX IF NOT EXISTS idx_search_region ON expanded_deals(search_region);
CREATE INDEX IF NOT EXISTS idx_price ON expanded_deals(price);

-- Helper table: scrape_runs
-- Track each scrape execution for audit/debugging
CREATE TABLE IF NOT EXISTS scrape_runs (
    id SERIAL PRIMARY KEY,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    origins_count INTEGER,
    cards_found INTEGER,
    expansions_attempted INTEGER,
    expansions_succeeded INTEGER,
    valid_deals INTEGER,
    status VARCHAR(20) DEFAULT 'running'  -- running, completed, failed
);

-- Index for scrape_runs
CREATE INDEX IF NOT EXISTS idx_scrape_runs_started ON scrape_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_scrape_runs_status ON scrape_runs(status);

