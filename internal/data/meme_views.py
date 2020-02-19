# This file is purely to contain the create statements for views that the Memes cog requires.
# There is no reason to make this a separate file other than to keep things slightly more clean looking.

view_b_five = """CREATE VIEW bottom_five 
                as 
                select author_id, author_username, avg(score) as average, c from(select author_id, author_username, avg(score) as score, count(author_id) as c from memes group by author_id) 
                WHERE c > 4 
                group by author_id 
                order by average asc 
                LIMIT 10"""

view_b_five_ab_ten = """CREATE VIEW bottom_five_above_ten
as
select author_id, author_username, avg(score) as average, c
from(
		select author_id, author_username, avg(score) as score, count(author_id) as c
		from memes 
		group by author_id
	) 
WHERE c > 9
group by author_id 
order by average asc
LIMIT 10"""

view_t_five = """CREATE VIEW top_five
as
select author_id, author_username, avg(score) as average, c
from(
		select author_id, author_username, avg(score) as score, count(author_id) as c
		from memes 
		group by author_id
	) 
WHERE c > 4
group by author_id 
order by average desc
LIMIT 10"""

view_t_five_above_ten = """CREATE VIEW top_ten_above_ten
as
select author_id, author_username, avg(score) as average, c
from(
		select author_id, author_username, avg(score) as score, count(author_id) as c
		from memes 
		group by author_id
	) 
WHERE c > 9
group by author_id 
order by average desc
LIMIT 10"""

view_get_meme_num = """CREATE VIEW get_meme_num
as
select row from (select row_number() over ( order by date_added ) row, m_id from memes) where m_id = 5"""

view_random_meme = """CREATE VIEW random_meme
as
SELECT *
FROM (select row, m_id, meme from (select row_number() over ( order by date_added ) row, m_id, meme from memes))
LIMIT 1
OFFSET ABS(RANDOM()) % MAX((SELECT COUNT(*) FROM memes), 1)"""

view_random_new_meme = """CREATE VIEW random_new_meme
as
SELECT *
FROM (select row, m_id, meme from (select row_number() over ( order by date_added ) row, m_id, meme from memes WHERE date_added BETWEEN date('now','-30 days') AND date('now')))
LIMIT 1
OFFSET ABS(RANDOM()) % MAX((SELECT COUNT(*) FROM (select row, m_id, meme from (select row_number() over ( order by date_added ) row, m_id, meme from memes WHERE date_added BETWEEN date('now','-30 days') AND date('now')))), 1)"""

view_random_unrated = """CREATE VIEW random_unrated
as
SELECT * FROM memes WHERE memes.score = 0 AND memes.m_id NOT IN (select m_id from upvotes)
LIMIT 1
OFFSET ABS(RANDOM()) % MAX((SELECT COUNT(*) FROM (SELECT * FROM memes WHERE memes.score = 0 AND memes.m_id NOT IN (select m_id from upvotes))), 1)"""
