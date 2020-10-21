-- name: get_post_given_url^
-- Get the post_id and media_hash associated with a url
SELECT post_id, media_hash FROM post WHERE url = :url;

-- name: get_labels_and_scores_for_post
-- Get the labels we already calculated for a post
SELECT label, score
  FROM post_label
 WHERE post_id = :post_id
   AND ts_del is NULL
 ORDER BY score DESC
;

-- name: did_we_already_repost^
-- If a post_id has already been reposted to social media then we'll get a row
SELECT post_id, label FROM top_post WHERE post_id = :post_id and label = :label;
