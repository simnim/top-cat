-- name: get_top_posts
-- Fetches the most recent 10 posts for a particular label
select
      p.url as media
    , p.title
    , p.timestamp_ins as noticed_at
from
        top_post tp
    join post p using (post_id)
where tp.label = :label
order by tp.timestamp_ins desc
limit 10;