import sqlite3
from flask import Flask, request, flash, render_template, g, abort, redirect, session, url_for
db_location = 'var/sqlite3v2.db'


# Running on and off database ##########################################################################################


def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = sqlite3.connect(db_location)
        g.db = db
    return db


def close_db_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


# Getting school(s) ####################################################################################################


def get_all_schools():
    db = get_db()
    sql = "SELECT * FROM schools"
    return db.cursor().execute(sql)


def get_school_by_schid(schid):
    db = get_db()
    sql = "SELECT * FROM schools where schid = ?"
    return db.cursor().execute(sql, [schid])


def get_schools_by_location(city):
    db = get_db()
    sql = "SELECT * FROM schools WHERE City= ?"
    return db.cursor().execute(sql, [city])


def get_schools_by_duration(duration):
    db = get_db()
    sql = "SELECT count(*) FROM programs WHERE Duration= ?"
    return db.cursor().execute(sql, [duration])


def get_first_school_by_schid(schid):
    db = get_db()
    sql = "SELECT * FROM schools where schid = ?"
    return db.cursor().execute(sql, [schid]).fetchone()


def get_school_name_by_schid(schid):
    db = get_db()
    sql = "SELECT name FROM schools where schid = ?"
    return db.cursor().execute(sql, [schid]).fetchone()


def get_school_count_by_location(city):
    db = get_db()
    sql = "SELECT count(*) FROM schools WHERE City= ?"
    return db.cursor().execute(sql, [city])


def get_school_count_by_duration(duration):
    db = get_db()
    sql = "SELECT count(*) FROM programs WHERE Duration= ?"
    return db.cursor().execute(sql, [duration])


def search_school(value):
    db = get_db()
    sql = "SELECT * FROM schools WHERE name LIKE ? OR city LIKE ? OR district LIKE ?"
    return db.cursor().execute(sql, ["%"+value+"%", value, value])


# Getting program(s) ###################################################################################################


def get_all_programs():
    db = get_db()
    sql = "SELECT * FROM programs"
    return db.cursor().execute(sql)


def get_prog_by_schid(schid):
    db = get_db()
    sql = "SELECT * FROM programs where schid = ?"
    return db.cursor().execute(sql, [schid])


def get_first_prog_by_schid(schid):
    db = get_db()
    sql = "SELECT * FROM programs where schid = ?"
    return db.cursor().execute(sql, [schid]).fetchone()


def get_prog_by_duration_and_schid(duration, schid):
    db = get_db()
    sql = "SELECT * FROM programs WHERE duration = ? AND schid = ?"
    return db.cursor().execute(sql, [duration, schid])


def get_prices_for_programs():
    db = get_db()
    sql = "SELECT duration, appli_fee, course_fee, acco_fee FROM programs"
    return db.cursor().execute(sql)


# Getting user(s) ######################################################################################################


def get_first_user_info_by_email(email):
    db = get_db()
    sql = "SELECT email, display_name, country FROM users WHERE email = ?"
    return db.cursor().execute(sql, [email]).fetchone()


def get_first_user_by_email(email):
    db = get_db()
    sql = "SELECT * FROM users WHERE email = ?"
    return db.cursor().execute(sql, [email]).fetchone()


def get_user_count_by_email(email):
    db = get_db()
    sql = "SELECT count(*) FROM users WHERE email = ?"
    return db.cursor().execute(sql, [email])


# Getting review(s) ####################################################################################################


def get_valide_reviews_by_schid(schid):
    db = get_db()
    sql = "SELECT * FROM reviews WHERE validated=1 AND schid= ?"
    return db.cursor().execute(sql, [schid])


def get_reviews_by_user_email(email):
    db = get_db()
    sql = "SELECT * FROM reviews WHERE user_email = ?"
    return db.cursor().execute(sql, [email])


def get_review_id(email, schid):
    db = get_db()
    sql = "SELECT rowid FROM reviews WHERE user_email = ? AND schid = ?"
    return db.cursor().execute(sql, (email, schid)).fetchone()


def is_review_given(schid, email):
    db = get_db()
    sql = "SELECT count(*) FROM reviews WHERE schid = ? AND user_email=?"
    return db.cursor().execute(sql, (schid, email)).fetchone()


# Getting favorite(s) ##################################################################################################


def get_favorite_by_user_email(email, limit=0):
    db = get_db()
    if limit == 0:
        sql = "SELECT schid FROM favorites WHERE user_email = ?"
        return db.cursor().execute(sql, [email]).fetchall()
    else:
        sql = "SELECT schid FROM favorites WHERE user_email = ? LIMIT ?"
        return db.cursor().execute(sql, (email, limit))


# Adding favorite(s) ###################################################################################################


def add_favorite(email, schid, proid=''):
    db = get_db()
    sql = "INSERT INTO favorites VALUES (?,?,?)"
    db.cursor().execute(sql, (email, schid, proid))
    db.commit()


# Adding user ##########################################################################################################


def add_user(email, password, displayName, country):
    db = get_db()
    sql = "INSERT INTO users VALUES (?,?,?,?,?)"
    db.cursor().execute(sql, (email, password, displayName, country, 1))
    db.commit()


# Adding review ########################################################################################################


def add_review(mail, score, content, schid):
    db = get_db()
    sql = "INSERT INTO reviews(user_email, note, content, validated, schid) VALUES(?,?,?,?,?)"
    db.cursor().execute(sql, (mail, score, content, 0, schid))
    db.commit()


# Checking favorites ###################################################################################################


def is_favorite_school(schid, email):
    db = get_db()
    sql = "SELECT * FROM favorites WHERE schid=? AND user_email=? AND progid=''"
    return db.cursor().execute(sql, (schid, email)).fetchone()


def is_favorite_program(schid, email):
    db = get_db()
    sql = "SELECT progid FROM favorites WHERE schid=? AND user_email=? AND progid!=''"
    return db.cursor().execute(sql, (schid, email))


# Deleting favorites ###################################################################################################
