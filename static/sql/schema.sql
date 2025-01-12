CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    email TEXT NOT NULL,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    auto_generated BOOLEAN
);

CREATE TABLE images (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    image BLOB,
    user_id INTEGER,
    classification TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
