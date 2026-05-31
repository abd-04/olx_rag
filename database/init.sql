CREATE TABLE IF NOT EXISTS listings (
    id             SERIAL PRIMARY KEY,
    title          TEXT NOT NULL,
    price_pkr      BIGINT NOT NULL,
    price_lakh     TEXT,
    city           TEXT,
    year           TEXT,
    km_driven      TEXT,
    fuel           TEXT,
    transmission   TEXT,
    vehicle_type   TEXT NOT NULL DEFAULT 'car',
    engine_cc      TEXT,
    description    TEXT,
    url            TEXT NOT NULL UNIQUE,
    embedding_text TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS listings_price_idx ON listings (price_pkr);
CREATE INDEX IF NOT EXISTS listings_vehicle_type_idx ON listings (vehicle_type);
CREATE INDEX IF NOT EXISTS listings_search_idx ON listings USING GIN (
    to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(description, ''))
);
