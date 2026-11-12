CREATE TABLE IF NOT EXISTS users (
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(50) NOT NULL UNIQUE,
    password   TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS games (
    game_id         UUID PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    player          INTEGER NOT NULL CHECK (player IN (0, 1)),
    cells           JSONB NOT NULL CHECK (jsonb_array_length(cells) = 9),
    game_running    BOOLEAN NOT NULL,
    winning_pattern JSONB CHECK (winning_pattern IS NULL OR jsonb_array_length(winning_pattern) = 3)
);
CREATE INDEX IF NOT EXISTS idx_games_user_id ON games(user_id);