-- name: record_post!
-- Stash metadata for the post found on /r/aww
INSERT INTO post (url, media_hash, title) values (:url, :media_hash, :title);

-- name: record_post_label!
-- Record all the labels above the minimum cutoff in the db
INSERT INTO post_label (post_id, label, score) values (:post_id, :label, :score);

-- name: record_the_repost!
-- We found a top cat/dog, record it so we only reshare it once
INSERT INTO top_post (post_id,label) values (:post_id, :label);

