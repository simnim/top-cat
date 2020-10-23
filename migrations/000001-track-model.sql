drop index media_media_hash_index;
drop index media_url_index;
drop index top_post_post_id_index;

alter table post rename to post_;
alter table post_label rename to post_label_;
alter table top_post rename to top_post_;

.read sql/schema.sql

insert into post(
    post_id,
    url,
    media_hash,
    title,
    ts_ins
)
select
    post_id,
    url,
    media_hash,
    title,
    timestamp_ins
from post_
;


insert into post_label (
    label_id,
    post_id,
    label,
    score,
    model,
    ts_ins
)
select
    pl.label_id,
    pl.post_id,
    pl.label,
    pl.score,
    'gvision_labeler',
    p.timestamp_ins
from post_label_ pl
join post_ p using (post_id)
;

insert into top_post (
    top_post_id,
    post_id,
    label,
    ts_ins
)
select
    top_post_id,
    post_id,
    label,
    timestamp_ins
from top_post_
;

drop table post_;
drop table post_label_;
drop table top_post_;
