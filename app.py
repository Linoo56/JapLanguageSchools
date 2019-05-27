import configparser
import bcrypt
import mail
import model
from functools import wraps
from school import School
from program import Program
from review import Review
from datetime import datetime
from flask import Flask, request, flash, render_template, g, abort, redirect, session, url_for
app = Flask(__name__)
config = configparser.ConfigParser()
config.read('etc/defaults.cfg')
app.secret_key = config.get('config', 'secret_key')
app.gmail_psw = config.get('config', 'gmail_psw')
db_location = 'var/sqlite3v2.db'


def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('logged_in', False)
        if not status:
            return redirect(url_for('root'))
        return f(*args, **kwargs)

    return decorated


def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        status = session.get('admin', False)
        if not status:
            return redirect(url_for('root'))
        return f(*args, **kwargs)

    return decorated


def get_db():
    return model.get_db()


@app.teardown_appcontext
def close_db_connection(exception):
    model.close_db_connection(exception)


@app.context_processor
def utility_processor():
    def format_price(value):
        if value != "":
            return "{:,.2f}".format(value)
        else:
            return value

    return dict(format_price=format_price)


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_ressource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_count_db_simple(sql):
    db = get_db()
    return db.cursor().execute(sql)


def init(app):
    config = configparser.ConfigParser()
    try:
        config_location = "etc/defaults.cfg"
        config.read(config_location)

        app.config['SECRET_KEY'] = config.get("config", "secret_key")
        app.config['GMAIL_PSW'] = config.get("config", "gmail_psw")
    except:
        return render_template('error.html')


@app.route('/')
def root():
    return render_template('home.html')


@app.route('/change-currency/<currency>/')
def change_currency(currency):
    session['currency'] = currency
    return redirect(request.referrer)


@app.route('/add-school/')
def add_school():
    return render_template('home.html')


@app.route('/schools/')
def listing_schools():
    schoolsdata = model.get_all_schools()
    schools = []
    for t in schoolsdata:
        schools.append(School(t[0], t[1], t[2], t[3], t[4], t[5]))
    return render_template('boxes.html', schools=schools)


@app.route('/programs/')
def listing_programs():
    schoolsdata = model.get_all_schools()
    schools = []
    for u in schoolsdata:
        schools.append(School(u[0], u[1], u[2], u[3], u[4], u[5]))
    programs = []
    for school in schools:
        programsdata = model.get_prog_by_schid(school.schid)
        for t in programsdata:
            programs.append([school, Program(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10])])
    return render_template('programBoxes.html', programs=programs)


@app.route('/schools/<schid>')
def school_description(schid):
    try:
        if session['currency'] == 'euros':
            currency = [130, 'euros']
        elif session['currency'] == 'pounds':
            currency = [145.5, 'pounds']
        elif session['currency'] == 'dollars':
            currency = [112, 'dollars']
        else:
            currency = [130, 'euros']
    except KeyError:
        currency = [130, 'euros']
    finally:
        schooldata = model.get_school_by_schid(schid)
        programsdata = model.get_prog_by_schid(schid)
        reviewsdata = model.get_valide_reviews_by_schid(schid)
        schoolprograms = []
        schoolreviews = []
        progfav = []
        for t in schooldata:
            print(t)
            school = School(t[0], t[1], t[2], t[3], t[4], t[5])
        for u in programsdata:
            schoolprograms.append(Program(u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10]))
        for v in reviewsdata:
            user = model.get_first_user_info_by_email(v[0])
            schoolreviews.append([Review(v[0], v[1], v[2], v[3], v[4], v[5], v[6]), user[1], user[2]])
        try:
            fav = model.is_favorite_school(schid, session['user'])
            progfavdata = model.is_favorite_program(schid, session['user'])
            for t in progfavdata:
                progfav.append(t[0])
            userreview = model.is_review_given(schid, session['user'])
            return render_template('description.html', currency=currency, school=school, programs=schoolprograms,
                                   reviews=schoolreviews, fav=fav, progfav=progfav, userReview=userreview[0])
        except KeyError:
            return render_template('description.html', currency=currency, school=school, programs=schoolprograms,
                                   reviews=schoolreviews)


@app.route('/schools/<schid>/submit-review', methods=['GET', 'POST'])
@requires_login
def submit_review(schid):
    if request.method == 'GET':
        schdata = model.get_school_by_schid(schid)
        school = School(schdata[0], schdata[1], schdata[2], schdata[3], schdata[4], schdata[5])
        return render_template('submitreview.html', school=school)
    else:
        score = request.form['score']
        content = request.form['review-content']
        school = model.get_school_name_by_schid([schid])
        model.add_review(session['user'], score, content, schid)
        reviewid = model.get_review_id(session['user'], schid)
        url = url_for(check_review) + str(reviewid[0])
        mail.send("Arekusandora78@gmail.com", app.gmail_psw, "Review Submission",
                  "A new review has been submited by " + session['user_name'] + " (" + session[
                      'user'] + ") about the school " + school[0] + ". Please check it out ! " + url)
        flash("Your review has been successfully sent")
        return redirect(url_for('school_description', schid=schid))


@app.route('/programs/price')
def prices():
    try:
        if session['currency'] == 'euros':
            currency = [130, 'euros']
        elif session['currency'] == 'pounds':
            currency = [145.5, 'pounds']
        elif session['currency'] == 'dollars':
            currency = [112, 'dollars']
        else:
            currency = [130, 'euros']
    except KeyError:
        currency = [130, 'euros']
    finally:
        prices = ['U1000', 'O1000']
        counts = [0, 0]
        values = []
        for result in model.get_prices_for_programs():
            if result[3] != '':
                if result[1] != '' and ((result[1] + result[2] + result[3]) / result[0]) / currency[0] < 1000:
                    counts[0] = counts[0] + 1
                elif result[1] == '' and ((result[2] + result[3]) / result[0]) / currency[0] < 1000:
                    counts[0] = counts[0] + 1
                else:
                    counts[1] = counts[1] + 1
        values.append([prices[0], counts[0]])
        values.append([prices[1], counts[1]])
        return render_template('pricecategories.html', prices=values, currency=currency)


@app.route('/programs/price/<price_range>')
def sort_prices(price_range):
    db = get_db()
    try:
        if session['currency'] == 'euros':
            currency = [130, 'euros']
        elif session['currency'] == 'pounds':
            currency = [145.5, 'pounds']
        elif session['currency'] == 'dollars':
            currency = [112, 'dollars']
        else:
            currency = [130, 'euros']
    except KeyError:
        currency = [130, 'euros']
    finally:
        selectedprograms = []
        programs = []
        programsdata = model.get_all_programs()
        for u in programsdata:
            programs.append(Program(u[0], u[1], u[2], u[3], u[4], u[5], u[6], u[7], u[8], u[9], u[10]))
        if price_range == 'U1000':
            for program in programs:
                if program.accoFee != '' and program.appliFee != '' and (
                        (program.appliFee + program.courseFee + program.accoFee) / program.duration) / currency[0]\
                        < 1000:
                    school = model.get_school_by_schid(program.schId)
                    for t in school:
                        selectedprograms.append([School(t[0], t[1], t[2], t[3], t[4], t[5]), program])
                if program.accoFee != '' and program.appliFee == '' and (
                        (program.courseFee + program.accoFee) / program.duration) / currency[0] < 1000:
                    school = model.get_school_by_schid(program.schId)
                    for t in school:
                        selectedprograms.append([School(t[0], t[1], t[2], t[3], t[4], t[5]), program])
        elif price_range == 'O1000':
            for program in programs:
                if program.accoFee != '' and program.appliFee == '' and (
                        (program.courseFee + program.accoFee) / program.duration) / currency[0] >= 1000:
                    school = model.get_school_by_schid(program.schId)
                    for t in school:
                        selectedprograms.append([School(t[0], t[1], t[2], t[3], t[4], t[5]), program])

                if program.accoFee != '' and program.appliFee != '' and (
                        (program.appliFee + program.courseFee + program.accoFee) / program.duration) / currency[0]\
                        >= 1000:
                    school = model.get_school_by_schid(program.schId)
                    for t in school:
                        selectedprograms.append([School(t[0], t[1], t[2], t[3], t[4], t[5]), program])
        return render_template('sortresultsprograms.html', programs=selectedprograms)


@app.route('/schools/city')
def cities():
    cities = ['Tokyo', 'Kyoto', 'Nagano', 'Fukuoka', 'Nagoya']
    values = []
    for city in cities:
        values.append([city, model.get_school_count_by_location(city)])
    return render_template('citycategories.html', cities=values)


@app.route('/schools/city/<city>')
def sort_cities(city):
    schools = []
    for t in model.get_schools_by_location(city):
        print(t)
        schools.append(School(t[0], t[1], t[2], t[3], t[4], t[5]))
    return render_template('sortresultsschools.html', schools=schools)


@app.route('/programs/duration')
def durations():
    durationsText = ['12months', '18months', '24months']
    durations = ["12", "18", "24"]
    values = []
    for num, duration in enumerate(durations):
        values.append([durationsText[num], model.get_school_count_by_duration(duration)])
    return render_template('durationcategories.html', durations=values)


@app.route('/programs/duration/<duration>')
def sort_durations(duration):
    schools = []
    programs = []
    value = ''
    if duration == '12months':
        value = '=12'
    elif duration == '18months':
        value = '=18'
    elif duration == '24months':
        value = '=24'
    else:
        abort(404)
    schoolsData = model.get_all_schools()
    for u in schoolsData:
        schools.append(School(u[0], u[1], u[2], u[3], u[4], u[5]))
    for school in schools:
        programsData = model.get_prog_by_duration_and_schid(value, school.schid)
        for t in programsData:
            programs.append([school, Program(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10])])
    return render_template('sortresultsprograms.html', programs=programs)


@app.route('/schools/search', methods=['POST'])
def search():
    value = request.form['value']
    schools = []
    schoolData = model.search_school(value)
    for u in schoolData:
        schools.append(School(u[0], u[1], u[2], u[3], u[4], u[5]))
    return render_template('searchresults.html', schools=schools, search=value)


@app.route('/register', methods=['GET'])
def register_page():
    return render_template('registerform.html')


@app.route('/register', methods=['POST'])
def registration():
    email = request.form['inputEmail']
    password = bcrypt.hashpw(str(request.form['inputPassword']).encode('utf8'), bcrypt.gensalt())
    displayName = request.form['inputDisplayName']
    country = request.form['inputCountry']
    count = model.get_user_count_by_email(email)
    if (count[0] == 0):
        model.add_user(email, password, displayName, country)
    else:
        flash("It seems that this email adress is already used")
        redirect(request.referrer)
    return render_template('registerform.html')


@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    msg = ""
    email = request.form['inputEmail']
    password = request.form['inputPassword']
    user = model.get_first_user_by_email(email)
    if user is not None :
        print (type(user[1]))
        if user[1] == bcrypt.hashpw(password.encode('utf-8'), user[1]):
            session['logged_in'] = True
            session['user'] = email
            session['user_name'] = user[2]
            if user[4] == 2:
                session['admin'] = True
                msg += "You are an admin"
            flash("Welcome back " + session['user_name'] + " !" + msg)
            return redirect(url_for('root'))
    flash("Your email and/or password is wrong")
    return render_template('login.html')



@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('logged_in', None)
    session.pop('user_name', None)
    session.pop('admin', None)
    return redirect(url_for('root'))


@app.route('/profile')
@requires_login
def profile():
    reviews = []
    user = model.get_first_user_info_by_email(session['user'])
    favorites = model.get_favorite_by_user_email(session['user'], 4)
    reviewsData = model.get_reviews_by_user_email(session['user'])
    for rd in reviewsData:
        theSchoolData = model.get_first_school_by_schid(rd[6])
        reviews.append([Review(rd[0], rd[1], rd[2], rd[3], rd[4], rd[5], rd[6]), theSchoolData[0]])
    return render_template('profile.html', user=user, favorites=favorites, reviews=reviews)


@app.route('/profile/favorites')
@requires_login
def favorites():
    favschools = []
    favorites = model.get_favorite_by_user_email(session['user'])
    for favorite in favorites:
        if favorite[2] == '':
            u = model.get_first_school_by_schid(favorite[1])
            favschools.append([1, School(u[0], u[1], u[2], u[3], u[4], u[5])])
        else:
            t = model.get_first_prog_by_schid(favorite[2])
            school = model.get_school_name_by_schid(favorite[1])
            favschools.append(
                [2, Program(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9], t[10]), school[0]])
    return render_template('favorites.html', favorites=favschools)


@app.route('/addfav/<schid>')
@requires_login
def add_school_favorite(schid):
    school = model.get_school_name_by_schid(schid)
    model.add_favorite(session['user'], schid)
    flash(school[0] + " has been added to your favorites schools")
    return redirect(request.referrer)


@app.route('/delfav/<schid>')
@requires_login
def del_school_favorite(schid):
    db = get_db()
    sql = "DELETE FROM favorites WHERE schid=? AND user_email=? AND progid=''"
    school = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [schid]).fetchone()
    db.cursor().execute(sql, (schid, session['user']))
    db.commit()
    flash(school[0] + " has been removed from your favorites schools")
    return redirect(request.referrer)


@app.route('/addfav/<schid>/<progid>')
@requires_login
def add_program_favorite(schid, progid):
    model.add_favorite(session['user'], schid, progid)
    flash("The program has been added to your favorites programs")
    return redirect(request.referrer)


@app.route('/delfav/<schid>/<progid>')
@requires_login
def del_program_favorite(schid, progid):
    db = get_db()
    sql = "DELETE FROM favorites WHERE schid=? AND progid = ? AND user_email=?"
    school = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [schid]).fetchone()
    db.cursor().execute(sql, (schid, progid, session['user']))
    db.commit()
    flash("The program has been removed from your favorites programs")
    return redirect(request.referrer)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        return render_template('contact.html')
    elif request.method == 'POST':
        type = request.form['inputType']
        message = request.form['inputMessage']
        if type == 'user':
           name = request.form['inputName']
           topic = request.form['inputTopic']
           mail.send("Arekusandora78@gmail.com", app.gmail_psw, "Contact from an user",
                     "You have been contacted by " + name + " about '"+topic+"' \n\n"+message)
        elif type == 'school':
           saveLink = 'static/uploads/upload.pdf'
           f = request.files['datafile']
           name = f.filename
           f.save(saveLink)
           schoolName = request.form['inputSchoolName']
           schoolTopic = request.form['inputSchoolTopic']
           url = url_for('check_document', filename=name.replace(' ','_'), _external=True)
           mail.send("Arekusandora78@gmail.com", app.gmail_psw, "Contact from a school",
                     "You have been contacted by " + schoolName + " about '" + schoolTopic + "' \n\n"+message+"\n\n"
                     "Attached document : "+request.url_root+saveLink+
                     "\n\n To register this document, please go to this link :"+url)
        return redirect(request.referrer)



# Fonctions admin
@app.route('/check-review/<reviewid>')
@requires_admin
def check_review(reviewid):
    db = get_db()
    reviewData = db.cursor().execute("SELECT * FROM reviews WHERE rowid = ? AND validated = 0", [reviewid]).fetchone()
    review = Review(reviewData[0], reviewData[1], reviewData[2], reviewData[3], reviewData[4], reviewData[5],
                    reviewData[6])
    schoolName = db.cursor().execute("SELECT name FROM schools WHERE schid = ?", [review.schid]).fetchone()
    userName = db.cursor().execute("SELECT display_name FROM users WHERE email = ?", [review.userEmail]).fetchone()
    return render_template('reviewchecking.html', reviewid=reviewid, review=review, school=schoolName[0],
                           user=userName[0])


@app.route('/check-review/<reviewid>/accept')
@requires_admin
def accept_review(reviewid):
    db = get_db()
    db.cursor().execute("UPDATE reviews SET validated = 1 WHERE rowid = ?", [reviewid])
    db.cursor().execute("UPDATE reviews SET validated_by = ? WHERE rowid = ?", (session['user_name'], reviewid))
    now = datetime.utcnow().strftime('%B %d %Y')
    db.cursor().execute("UPDATE reviews SET validation_date = ? WHERE rowid = ?", (now, reviewid))
    db.commit()
    schid = db.cursor().execute("SELECT schid FROM reviews WHERE rowid = ?", [reviewid]).fetchone()

    flash("The review has been accepted")
    return redirect(url_for('school_description', schid=schid[0]))


@app.route('/check-review/<reviewid>/refuse')
@requires_admin
def refuse_review(reviewid):
    db = get_db()
    db.cursor().execute("UPDATE reviews SET validated = 2 WHERE rowid = ?", [reviewid])
    db.commit()
    schid = db.cursor().execute("SELECT schid FROM reviews WHERE rowid = ?", [reviewid]).fetchone()
    flash("The review has been refused")
    return redirect(url_for('school_description', schid=schid[0]))


@app.route('/check-document/<filename>')
@requires_admin
def check_document(filename):
    return render_template('documentchecking.html', filename=filename)


'''@app.route('check-document/<filename>/accept')
@requires_admin
def accept_doc(filename):



@app.route('check-document/<filename>/refuse')
@requires_admin
def refuse_doc(filename):'''


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html'), 404


if __name__ == '__main__':
    init(app)
    app.run(host="0.0.0.0", debug=True)
