# Study Tracker

A Flask web app for tracking study topics, built during my internship.

## Features
- User login and sessions
- Topic management backed by MySQL
- Email reminders using a background scheduler (APScheduler)

## Tech Stack
Python, Flask, MySQL, APScheduler, HTML/CSS/JS

## Setup
1. Clone the repo
2. `pip install -r requirements.txt`
3. Create a `.env` file with `SECRET_KEY`, `MYSQL_PASSWORD`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`
4. Run `python main.py`
