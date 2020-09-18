-- name: create_schema#
CREATE TABLE IF NOT EXISTS
post (
    post_id       INTEGER PRIMARY KEY,
    timestamp_ins text not null default current_timestamp,
    url           text not null,
    media_hash    text not null,
    title         text not null
);

CREATE TABLE IF NOT EXISTS
post_label (
    label_id      INTEGER PRIMARY KEY,
    post_id       int not null,
    label         text not null,
    score         REAL,
    FOREIGN KEY(post_id) REFERENCES post(post_id)
);

CREATE TABLE IF NOT EXISTS
top_post (
    top_post_id   INTEGER PRIMARY KEY,
    post_id       int not null,
    label         text not null,
    timestamp_ins text not null default current_timestamp,
    FOREIGN KEY(post_id) REFERENCES post(post_id)
);

CREATE INDEX IF NOT EXISTS
media_media_hash_index
on  post (
        media_hash
    );

CREATE INDEX IF NOT EXISTS
media_url_index
on  post (
        url
    );

CREATE INDEX IF NOT EXISTS
top_post_post_id_index
on  top_post (
        post_id
    );
