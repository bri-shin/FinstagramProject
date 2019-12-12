from flask import Flask, render_template, request, session, redirect, url_for, send_file, abort
# from flask_table import Table, Col
import json
import os
import uuid
import hashlib
import pymysql.cursors
from functools import wraps
import time
from datetime import datetime
from table import Results, followTable, likeTable, Analytics_Reactions, Analytics_Rating, Tag_Table, commentTable, followerTable


app = Flask(__name__)
app.secret_key = "super secret key"
IMAGES_DIR = os.path.join(os.getcwd(), "images")

connection = pymysql.connect(host="localhost",
                             user="root",
                             password="root",
                             db="finsta",
                             charset="utf8mb4",
                             port=3306,
                             cursorclass=pymysql.cursors.DictCursor,
                             autocommit=True)


def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not "username" in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return dec


@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


@app.route("/home", methods=["GET"])
@login_required
def home():
    with connection.cursor() as cursor:
        # display photos visible to user.
        username = session['username']  # checked: correctly retrieves username
        query = '''
                SELECT photoID, photoPoster
                FROM Photo
                WHERE allFollowers = True AND %s in (SELECT username_follower FROM Follow WHERE username_followed = Photo.photoPoster and followstatus=1)
                    OR %s in (SELECT member_username FROM BelongTo NATURAL JOIN SharedWith WHERE SharedWith.photoID = Photo.photoID)
                ORDER BY postingdate DESC
                '''
        cursor.execute(query, (username, username))
    contentitems = cursor.fetchall()
    table = Results(contentitems)
    table.border = True
    return render_template("home.html", username=session['username'], table=table)

# december 6 5pm working version
# @app.route("/upload", methods=["GET"])
# @login_required
# def upload():
#     return render_template("upload.html")


@app.route("/upload", methods=["GET"])
@login_required
def upload():
    with connection.cursor() as cursor:
        username = session['username']
        query = '''
            SELECT groupName FROM BelongTo WHERE member_username = %s
        '''
        cursor.execute(query, (username))
    group_names = cursor.fetchall()
    return render_template("upload.html", group_names=group_names)


@app.route("/images", methods=["GET"])
@login_required
def images():
    username = session['username']
    query = ''' SELECT * FROM photo
                WHERE allFollowers = True AND %s in (SELECT username_follower FROM Follow WHERE username_followed = Photo.photoPoster and followstatus=1)
                OR %s in (SELECT member_username FROM BelongTo NATURAL JOIN SharedWith WHERE SharedWith.photoID = Photo.photoID)
    '''

    with connection.cursor() as cursor:
        cursor.execute(query, (username, username))
        data = cursor.fetchall()

    return render_template("images.html", images=data)


@app.route("/images/<photoID>", methods=["GET", "POST"])
def imageDetail(photoID):
    username = session['username']
    query = ''' SELECT * FROM photo
                WHERE photoID=%s
    '''

    query2 = '''SELECT username, rating FROM Likes NATURAL JOIN photo
                WHERE photoID=%s
    '''
    query3 = '''
            SELECT username, fname, lname
            FROM Tagged NATURAL JOIN Person
            WHERE photoID = %s AND tagstatus = 1
    '''

    queryComment = '''SELECT username, comment
                FROM Comments
                WHERE photoID=%s
    '''

    with connection.cursor() as cursor:

        # Finding Photo and Photo Information
        cursor.execute(query, (photoID))
        data = cursor.fetchall()[0]

        # Finding Ratings
        cursor.execute(query2, (photoID))
        likes = cursor.fetchall()
        table = likeTable(likes)

        # Finding Comments
        cursor.execute(queryComment, (photoID))
        comments = cursor.fetchall()
        commentResults = commentTable(comments)
        commentResults.border = True

        # Finding Tags
        cursor.execute(query3, (photoID))
        tagged = cursor.fetchall()
        table1 = Tag_Table(tagged)
    table.border = True
    table1.border = True

    if request.form and "rating" in request.form:
        rating = request.form["rating"]
        now = datetime.now()

        with connection.cursor() as cursor:
            # Check if user already gave a rating before
            queryCheck = "SELECT username FROM Likes WHERE photoID=%s"
            cursor.execute(queryCheck, (photoID))
            existingNames = cursor.fetchall()
            new = True
            for names in existingNames:
                if username in names['username']:
                    new = False

            if not new:
                queryExist = '''UPDATE Likes
                                Set rating=%s
                                WHERE username=%s and photoID=%s
                '''

                cursor.execute(queryExist, (rating, username,photoID))

            else:
                # For Creating A Rating / Like
                query4 = ''' INSERT INTO Likes (username,photoID,liketime,rating)
                            VALUES (%s, %s, %s, %s)
                '''
                cursor.execute(query4, (username, photoID,
                                        now.strftime('%Y-%m-%d %H:%M:%S'), rating))

        return redirect(url_for("imageDetail", photoID=photoID))

    if request.form and "userComment" in request.form:
        now = datetime.now()
        comment = request.form["userComment"]

        with connection.cursor() as cursor:

            # For Creating A Comment
            query5 = ''' INSERT INTO Comments (username, photoID, commentTime, comment)
                        VALUES (%s, %s, %s, %s)
            '''

            cursor.execute(query5, (username, photoID,
                                    now.strftime('%Y-%m-%d %H:%M:%S'), comment))

        return redirect(url_for("imageDetail", photoID=photoID))

    else:
        return render_template("imageDetail.html", image=data, table=table, table1=table1, photoID=photoID, commentResults=commentResults)


@app.route("/image/<image_name>", methods=["GET"])
def image(image_name):
    image_location = os.path.join(IMAGES_DIR, image_name)
    if os.path.isfile(image_location):
        return send_file(image_location, mimetype="image/jpg")


@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")


# UNHASHED
# @app.route("/loginAuth", methods=["POST"])
# def loginAuth():
#     if request.form:
#         requestData = request.form
#         username = requestData["username"]
#         plaintextPasword = requestData["password"]
#         # hashedPassword = hashlib.sha256(
#         #     plaintextPasword.encode("utf-8")).hexdigest()
#
#         with connection.cursor() as cursor:
#             query = "SELECT * FROM person WHERE username = %s AND password = %s"
#             cursor.execute(query, (username, plaintextPasword))
#         data = cursor.fetchone()
#         if data:
#             session["username"] = username
#             return redirect(url_for("home"))
#
#         error = "Incorrect username or password."
#         return render_template("login.html", error=error)
#
#     error = "An unknown error has occurred. Please try again."
#     return render_template("login.html", error=error)


@app.route("/loginAuth", methods=["POST"])
def loginAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(
            plaintextPasword.encode("utf-8")).hexdigest()

        with connection.cursor() as cursor:
            query = "SELECT * FROM person WHERE username = %s AND password = %s"
            cursor.execute(query, (username, hashedPassword))
        data = cursor.fetchone()
        if data:
            session["username"] = username
            return redirect(url_for("home"))

        error = "Incorrect username or password."
        return render_template("login.html", error=error)

    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error=error)


@app.route("/registerAuth", methods=["POST"])
def registerAuth():
    if request.form:
        requestData = request.form
        username = requestData["username"]
        plaintextPasword = requestData["password"]
        hashedPassword = hashlib.sha256(
            plaintextPasword.encode("utf-8")).hexdigest()
        firstName = requestData["fname"]
        lastName = requestData["lname"]

        try:
            with connection.cursor() as cursor:
                query = "INSERT INTO Person (username, password, fname, lname) VALUES (%s, %s, %s, %s)"
                cursor.execute(
                    query, (username, hashedPassword, firstName, lastName))
        except pymysql.err.IntegrityError:
            error = "%s is already taken." % (username)
            return render_template('register.html', error=error)

        return redirect(url_for("login"))

    error = "An error has occurred. Please try again."
    return render_template("register.html", error=error)


@app.route("/logout", methods=["GET"])
def logout():
    session.pop("username")
    return redirect("/")


# december 6 5pm working version
# @app.route("/uploadImage", methods=["POST"])
# @login_required
# def upload_image():
#     if request.files:
#         image_file = request.files.get("imageToUpload", "")
#         image_name = image_file.filename
#         filepath = os.path.join(IMAGES_DIR, image_name)
#         image_file.save(filepath)
#         # query = "INSERT INTO photo (timestamp, filePath) VALUES (%s, %s)"
#         query = "INSERT INTO photo (postingdate, filePath) VALUES (%s, %s)"
#         with connection.cursor() as cursor:
#             cursor.execute(query, (time.strftime(
#                 '%Y-%m-%d %H:%M:%S'), image_name))
#         message = "Image has been successfully uploaded."
#         return render_template("upload.html", message=message)
#     else:
#         message = "Failed to upload image."
#         return render_template("upload.html", message=message)

@app.route("/uploadImage", methods=["POST"])
@login_required
def upload_image():
    username = session['username']
    if request.files:
        image_file = request.files.get("imageToUpload", "")
        image_name = image_file.filename
        filepath = os.path.join(IMAGES_DIR, image_name)
        image_file.save(filepath)
        now = datetime.now()
        if request.form:
            visibility = int(request.form["visibility"])

            # ------- Not Needed Since allFollowers is already an int
            # visibility_boolean = True
            # if visibility == 1:
            #     visibility_boolean = True
            # elif visibility == 2:
            #     visibility_boolean = False

            if visibility != 0 and visibility != 1:
                message = "Didn't select visibility option."
                return render_template("upload.html", message=message)
            query = "INSERT INTO photo (postingdate, filePath, allFollowers, photoPoster) VALUES (%s, %s, %r, %s)"

            with connection.cursor() as cursor:
                cursor.execute(query, (now.strftime(
                    '%Y-%m-%d %H:%M:%S'), image_name, visibility, username))
                if visibility == 0:

                    group_name = request.form["g_names"]  # checked
                    query1 = "SELECT photoID FROM photo WHERE photoID = (SELECT MAX(photoID) FROM photo)"

                    # Potential Issue here: there might be groups with the same name
                    query2 = "SELECT groupOwner FROM Friendgroup WHERE groupName=%s"
                    query3 = "INSERT INTO SharedWith (groupName, groupOwner, photoID) VALUES (%s,%s,%r)"
                    cursor.execute(query1)
                    photo_id = cursor.fetchall()[0]
                    cursor.execute(query2, (group_name))
                    groupOwner = cursor.fetchall()[0]
                    cursor.execute(
                        query3, (group_name, groupOwner["groupOwner"], photo_id["photoID"]))

            message = "Image has been successfully posted with visibility set to: " + \
                str(visibility)
            return render_template("uploadSuccess.html", message=message)

        else:
            message = "Didn't select visibility option."
            return render_template("upload.html", message=message)
    else:
        message = "Failed to upload image."
        return render_template("upload.html", message=message)


@app.route("/follow", methods=["GET"])
def follow():
    currentUser = session['username']
    query = "SELECT username_followed, username_follower FROM Follow WHERE username_followed=%s and followstatus=0"
    query2 = "SELECT username_followed FROM Follow WHERE username_follower = %s"
    with connection.cursor() as cursor:
        cursor.execute(query, (currentUser))
        contentitems = cursor.fetchall()
        table = followTable(contentitems)
        table.border = True

        cursor.execute(query2, (currentUser))
        followings = cursor.fetchall()
        followers = followerTable(followings)
        followers.border = True

    return render_template("follow.html", table=table, followers=followers)


@app.route("/followAuth", methods=["POST"])
def followAuth():
    if request.form:
        requestData = request.form
        toFollow = requestData["username"]
        currentUser = session['username']
        # Sending a follow request
        query = "INSERT INTO Follow (username_followed, username_follower, followstatus) VALUES (%s, %s, 0)"

        with connection.cursor() as cursor:
            cursor.execute(query, (toFollow, currentUser))

        return render_template("follow.html")


@app.route("/followAccept/<username>", methods=['GET', 'POST'])
def followAccept(username):
    currentUser = session['username']
    query = "UPDATE Follow SET followstatus=1 WHERE username_followed=%s and username_follower=%s and followstatus=0"
    with connection.cursor() as cursor:
        cursor.execute(query, (currentUser, username))
    return render_template("followAccept.html", username=username)


@app.route("/followAuth/<username>", methods=['GET', 'POST'])
def followDecline(username):
    currentUser = session['username']
    query = "DELETE FROM Follow WHERE username_followed=%s and username_follower=%s and followstatus=0"
    with connection.cursor() as cursor:
        cursor.execute(query, (currentUser, username))
    return render_template("followDecline.html", username=username)


@app.route("/search", methods=['GET', 'POST'])
def search():
    return render_template("search.html")


@app.route("/displaySearch", methods=['GET', 'POST'])
def displaySearch():
    if request.form:
        requestData = request.form
        search_user = requestData["username"]
    with connection.cursor() as cursor:
        # display photos visible to user.
        username = session['username']  # checked: correctly retrieves username
        query = '''
                SELECT *
                FROM Photo
                WHERE photoID IN
                    (SELECT photoID
                    FROM Photo
                    WHERE allFollowers = True AND %s IN (SELECT username_follower FROM Follow WHERE username_followed = Photo.photoPoster)
                        OR %s IN (SELECT member_username FROM BelongTo NATURAL JOIN SharedWith WHERE SharedWith.photoID = Photo.photoID))
                AND photoPoster = %s
                '''
        cursor.execute(query, (username, username, search_user))
    data = cursor.fetchall()
    return render_template("images.html", images=data)


@app.route("/analytics", methods=['GET', 'POST'])
def analytics():
    with connection.cursor() as cursor:
        # display photos visible to user.
        username = session['username']  # checked: correctly retrieves username
        query = '''
        SELECT photoID, photoPoster, COUNT(photoID) as display_likes
        FROM Photo NATURAL JOIN Likes
        GROUP BY photoID
        HAVING display_likes = (SELECT MAX(likes)
            FROM (SELECT photoID, COUNT(photoID) AS likes
                FROM Likes
                GROUP BY photoID) AS t1
            )
        '''
        query2 = '''
        SELECT photoID, photoPoster, SUM(rating) as tot_rating
        FROM Photo NATURAL JOIN Likes
        GROUP BY photoID
        HAVING tot_rating = (SELECT MAX(s_rating)
            FROM (SELECT photoID, SUM(rating) AS s_rating
                FROM Likes
                GROUP BY photoID) AS t1
            )
        '''
        cursor.execute(query)
        results1 = cursor.fetchall()
        table1 = Analytics_Reactions(results1)
        table1.border = True
        cursor.execute(query2)
        results2 = cursor.fetchall()
        table2 = Analytics_Rating(results2)
        table2.border = True
        return render_template("analytics.html", table1=table1, table2=table2)


if __name__ == "__main__":
    if not os.path.isdir("images"):
        os.mkdir(IMAGES_DIR)
    app.run()
    # app.run(use_reloader=True)
