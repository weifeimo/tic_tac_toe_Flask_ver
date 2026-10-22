CREATE TABLE IF NOT EXISTS games (
    game_id         UUID PRIMARY KEY,
    player          INTEGER NOT NULL CHECK (player IN (0, 1)),
    cells           JSONB NOT NULL CHECK (jsonb_array_length(cells) = 9),
    game_running    BOOLEAN NOT NULL,
    winning_pattern JSONB CHECK (winning_pattern IS NULL OR jsonb_array_length(winning_pattern) = 3)
);