-- Created the database
CREATE DATABASE referral;

-- Create the tables
CREATE TABLE users(
   username varchar(20) PRIMARY KEY,
   password varchar(30)
);

CREATE TABLE redemption (
	 username VARCHAR(20),
	 timestamp TIMESTAMP,
	 PRIMARY KEY (username, timestamp),
	 FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE transaction (
	 user1 VARCHAR(20),
	 user2 VARCHAR(20),
	 timestamp TIMESTAMP,
	 amount INT,
	 message VARCHAR,
	 PRIMARY KEY (user1, user2, timestamp),
	 FOREIGN KEY (user1) REFERENCES users(username),
	 FOREIGN KEY (user2) REFERENCES users(username)
);

CREATE TABLE account (
	 username VARCHAR(20) PRIMARY KEY,
	 to_give INT,
	 to_redeem INT,
	 FOREIGN KEY (username) REFERENCES users(username)
);





