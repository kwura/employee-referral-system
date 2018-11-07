-- insert the first users 
INSERT INTO users (username, password) VALUES
	('admin', '-804589398'),
	('user1', '-226369247'),
	('user2', '412121126'),
	('user3', '-1716579489'),
	('user4', '-1302926236'),
	('user5', '1421746429');

--  stored procedure
CREATE FUNCTION Insert_into_table(_user1 VARCHAR(20), _amount INT, _user2 VARCHAR(20), _message VARCHAR(50))
      RETURNS void AS
      $BODY$
          BEGIN
            INSERT INTO transaction(user1, user2, timestamp, amount, message)
            VALUES(_user1, _user2, current_timestamp, _amount, _message);

            UPDATE account SET to_give = to_give - _amount WHERE username = _user1;
            UPDATE account SET to_redeem = to_redeem + _amount WHERE username = _user2;

          END;
      $BODY$
      LANGUAGE 'plpgsql' VOLATILE
      COST 100;
-- trigger
CREATE OR REPLACE FUNCTION  trigger_me()
      RETURNS TRIGGER AS
      $BODY$
          BEGIN
            INSERT INTO redemption(username, timestamp)
            VALUES(NEW.username, current_timestamp);
           RETURN NEW;
          END;
      $BODY$
      LANGUAGE 'plpgsql' VOLATILE
      COST 100;

CREATE TRIGGER trigger_red
AFTER UPDATE ON account
FOR EACH ROW
WHEN (OLD.to_redeem = NEW.to_redeem + 10000) 
EXECUTE PROCEDURE trigger_me();

-- test trigger
UPDATE account SET to_redeem = to_redeem - 10000 WHERE username = 'user3';


-- insert the first account
INSERT INTO account (username, to_give, to_redeem) VALUES
	('user1', 1000, 20000),
	('user2', 1000, 30000),
	('user3', 1000, 40000),
	('user4', 1000, 50000),
	('user5', 1000, 60000);

-- calling the stored procedure
select * from Insert_into_table('user1', 500,'user2','good job');

-- insert data for redemption
INSERT INTO redemption (username, timestamp) VALUES
	('user1', '2018-09-07 12:05:24.44513-06'),
	('user1', '2018-10-07 12:06:24.44513-06'),
	('user2', '2018-09-07 12:07:24.44513-06'),
	('user2', '2018-10-07 12:08:24.44513-06'),
	('user3', '2018-09-07 12:09:24.44513-06'),
	('user3', '2018-10-07 12:20:24.44513-06'),
	('user4', '2018-09-07 12:23:24.44513-06'),
	('user4', '2018-10-07 12:01:24.44513-06'),
	('user5', '2018-09-07 12:35:24.44513-06');

-- insert transactional data 
INSERT INTO transaction(user1, user2, timestamp, amount, message) VALUES 
	('user1', 'user2','2018-09-07 11:05:24.44513-06', 750, 'nice bro'),
	('user1', 'user3','2018-10-07 11:06:24.44513-06', 800, 'nice work'),
	('user2', 'user4','2018-09-07 11:07:24.44513-06', 110, 'nice cool'),
	('user2', 'user1','2018-10-07 11:08:24.44513-06', 120, 'nice sick'),
	('user3', 'user2','2018-09-07 11:09:24.44513-06', 130, 'nice nasy'),
	('user3', 'user1','2018-10-07 11:20:24.44513-06', 150, 'nice thanks'),
	('user4', 'user5','2018-09-07 11:23:24.44513-06', 1000, 'nice appreciate it'),
	('user4', 'user3','2018-10-07 11:01:24.44513-06', 300, 'nice haha'),
	('user5', 'user2','2018-09-07 11:35:24.44513-06', 400, 'nice bra');

--One that shows the aggregate usage of points on a monthly basis – both rewards given out
 -- and rewards cashed in, as well as broken down by user, ranked in order of most points received to least
 SELECT EXTRACT(YEAR FROM timestamp) as year, EXTRACT(MONTH FROM timestamp) as month, count(*) * 10000 as points_cashed_in
    FROM redemption
    GROUP BY EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp)
    ORDER BY 1, 2;

 SELECT EXTRACT(YEAR FROM timestamp) as year, EXTRACT(MONTH FROM timestamp) as month, SUM(amount) as points_given_out
    FROM transaction
    GROUP BY EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp)
    ORDER BY 1, 2;

 
 SELECT to_char(timestamp, 'YYYY-MM') as year_month, SUM(amount) as points_received, user2
    FROM transaction
    GROUP BY year_month, user2
    ORDER BY 1, 2 DESC;

SELECT SUM(amount) as total_points_received, user2
    FROM transaction
    GROUP BY  user2
    ORDER BY 1 DESC;

-- o	One that shows who isn’t giving out all of their points for 
-- the most recent month only (including those that haven’t used any) 
SELECT username, to_give FROM account
WHERE to_give != 0
ORDER BY 2 DESC;

SELECT username, to_redeem
FROM account
WHERE username NOT IN (SELECT username FROM redemption WHERE EXTRACT(YEAR FROM timestamp) = EXTRACT(YEAR FROM NOW()) AND 
EXTRACT(MONTH FROM timestamp) = EXTRACT(MONTH FROM NOW())
);


-- o	One that shows all redemptions, by month by user, for the previous two months
SELECT to_char(timestamp, 'YYYY-MM') as month_year, username 
FROM redemption WHERE timestamp > current_date - INTERVAL '3 months' and
 EXTRACT(month from timestamp) != EXTRACT(month from NOW())
 ORDER BY 1,2;