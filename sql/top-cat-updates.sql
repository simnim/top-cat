-- name: invalidate_labels_for_post!
-- For manually overriding labels, first we need to discard automatic labels
UPDATE post_label
   set ts_del = current_timestamp
 where post_id = :post_id
   and ts_del is null
;
