CREATE TABLE IF NOT EXISTS listings (
    id            SERIAL PRIMARY KEY,
    title         TEXT,
    price_pkr     BIGINT,
    price_lakh    TEXT,
    city          TEXT,
    year          TEXT,
    km_driven     TEXT,
    fuel          TEXT,
    transmission  TEXT,
    description   TEXT,
    url           TEXT,
    embedding_text TEXT
);