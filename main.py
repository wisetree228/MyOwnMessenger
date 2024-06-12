from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, redirect, session, send_file, make_response, session
import psycopg2
from werkzeug.utils import secure_filename
from io import BytesIO
from random import choice


# functions for work with database
def execute(query):
    try:
        con = psycopg2.connect(
            database='base',
            host='localhost',
            user='postgres',
            password='123456789',

        )
        cur=con.cursor()
        cur.execute(query)
        con.commit()
        cur.close()
        con.close()
    except Exception as e:
        print('Ошибка:', e)


def executeAll(query):
    try:
        con=psycopg2.connect(
            database='base',
            host='localhost',
            user='postgres',
            password='123456789',

        )
        cur=con.cursor()
        cur.execute(query)
        l=cur.fetchall()
        cur.close()
        con.close()
        return l
    except Exception as e:
        print('Ошибка:', e)


def executeOne(query):
    try:
        con=psycopg2.connect(
            database='base',
            host='localhost',
            user='postgres',
            password='123456789',

        )
        cur=con.cursor()
        cur.execute(query)
        l=cur.fetchone()
        cur.close()
        con.close()
        return l
    except Exception as e:
        print('Ошибка:', e)


def checkId(query):
    try:
        con=psycopg2.connect(
            database='base',
            host='localhost',
            user='postgres',
            password='123456789',

        )
        cur=con.cursor()
        cur.execute(query)
        l=cur.fetchall()
        cur.close()
        con.close()
        if len(l) == 0:
            return False
        return True
    except Exception as e:
        print('Ошибка:', e)


def setimg(query, file):
    try:
        con = psycopg2.connect(
            database='base',
            host='localhost',
            user='postgres',
            password='123456789',

        )
        cur=con.cursor()
        cur.execute(query, (psycopg2.Binary(file),))
        con.commit()
        cur.close()
        con.close()
    except Exception as e:
        print('Ошибка:', e)

# random key generator
def getRandomKey():
    l = 'qwertyuioplkjhgfdsazxcvbnm1234567890'
    s = ''
    for i in range(10):
        s += choice(l)
    return s



app=Flask(__name__)
app.secret_key='key123456789'



# creating tables in database if they don't exist
execute('''
CREATE TABLE IF NOT EXISTS chats (
    user1 TEXT,
    user2 TEXT
);
''')

execute('''
CREATE TABLE IF NOT EXISTS groups (
    name TEXT,
    admin TEXT,
    members TEXT
);
''')

execute('''
CREATE TABLE IF NOT EXISTS images (
    key TEXT,
    img BYTEA
);
''')

execute('''
CREATE TABLE IF NOT EXISTS mess (
    text TEXT,
    auth TEXT,
    get TEXT,
    key TEXT
);
''')

execute('''
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT,
    img BYTEA
);
''')



# main page handler
@app.route('/')
def index():

    links=[] # arrays of chats and groups that user have
    groups=[]
    if 'userName' in session:
        chats = executeAll(f"SELECT * FROM chats WHERE user1='{session['userName']}' OR user2='{session['userName']}'")
        for i in chats:
            if i[0]==session['userName']:

                if executeOne(f"SELECT img FROM users WHERE username='{i[1]}';")[0]:
                    links.append([i[1], 1])
                else:
                    links.append([i[1], 0])
            else:

                if executeOne(f"SELECT img FROM users WHERE username='{i[1]}';")[0]:
                    links.append([i[0], 1])
                else:
                    links.append([i[0], 0])
        gr=executeAll(f"SELECT * FROM groups;")

        for i in gr:
            if i[1]==session['userName'] or session['userName'] in i[2]:
                groups.append(i[0])



    return render_template('index.html', session=session, links=links, groups=groups)

# login page handler
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        if len(username)>=5 and len(password)>=5 and not("'" in username or "'" in password): # check correct data
            if not checkId(f"SELECT * FROM users WHERE username='{username}'"):
                flash("That account doesn't exist!")
            else:
                user=executeOne(f"SELECT * FROM users WHERE username='{username}'")
                if user[2]!=password:
                    flash('Incorrect password!!')
                else:
                    session['userName']=username
                    return redirect(url_for('index'))
        else:
            flash("The length of the login and password is at least 5 characters, it is forbidden to use ' in order to protect against sql injections!")
    return render_template('login.html')


# registration page handler
@app.route('/register', methods=['POST', 'GET'])
def reg():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        if len(username)>=5 and len(password)>=5 and not("'" in username or "'" in password):
            if checkId(f"SELECT * FROM users WHERE username='{username}'"):
                flash('that account already exists!')
            else:
                execute(f"INSERT INTO users (username, password) VALUES ('{username}', '{password}');")

                session['userName']=username
                return redirect(url_for('index'))
        else:
            flash("The length of the login and password is at least 5 characters, it is forbidden to use ' in order to protect against sql injections!")
    return render_template('reg.html')

# logout handler
@app.route('/logout')
def logout():
    session.pop('userName', None)
    return redirect(url_for('index'))

# page for create a new chat with other user
@app.route('/newchat', methods=['POST', 'GET'])
def newchat():
    if not 'userName' in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        if not "'" in request.form['chat-name']:
            name=request.form['chat-name']
            if not checkId(f"SELECT * FROM users WHERE username='{name}';"):
                flash("that user doesn't exist!")
            elif checkId(f"SELECT * FROM chats WHERE user1='{session['userName']}' AND user2='{name}';") or checkId(f"SELECT * FROM chats WHERE user2='{session['userName']}' AND user1='{name}';"):
                flash("you already have a chat with this user!")
            elif name==session['userName']:
                flash("You can't have a chat with yourself!")
            else:
                execute(f"INSERT INTO chats (user1, user2) VALUES ('{session['userName']}', '{name}');")
                return redirect(url_for('chat', username=name))
        else:
            flash("don't use ' for SQL injections!")
    return render_template('newchat.html')


# getting image from message by key
@app.route('/get_img/<k>')
def get_img(k):

    image_data = executeOne(f"SELECT img FROM images WHERE key='{k}';")[0]

    if image_data:

        return send_file(
            BytesIO(image_data),
            mimetype='image/png'
        )
    else:
        image_data = executeOne(f"SELECT img FROM users WHERE username='empty';")[0]
        return send_file(
            BytesIO(image_data),
            mimetype='image/png'
        )


# chat page handler
@app.route('/chat/<username>', methods=['POST', 'GET'])
def chat(username):
    if not 'userName' in session:
        return redirect(url_for('index'))
    if not(checkId(f"SELECT * FROM chats WHERE user1='{session['userName']}' AND user2='{username}';") or checkId(f"SELECT * FROM chats WHERE user2='{session['userName']}' AND user1='{username}';")):
        return redirect('error')

    if username==session['userName']:
        return redirect(url_for('index'))

    if request.method=='POST':
        text=request.form['text']
        if text!='':
            if "'" in text:
                flash("don't use ' for SQL injections!")
            else:
                execute(f"INSERT INTO mess (text, auth, get) VALUES ('{text}', '{session['userName']}', '{username}');")

        elif 'image' in request.files:
            image = request.files['image']
            filename = secure_filename(image.filename)
            image_data = image.read()
            key=getRandomKey()
            execute(f"INSERT INTO mess (auth, get, key) VALUES ('{session['userName']}', '{username}', '{key}');")
            setimg(f"INSERT INTO images (key, img) VALUES ('{key}', (%s))", image_data)

    mess=executeAll(f"SELECT * FROM mess WHERE (auth='{session['userName']}' AND get='{username}') OR (auth='{username}' AND get='{session['userName']}')")

    return render_template('chat.html', mess=mess, username=username)




# profile page handler
@app.route('/profile', methods=['POST', 'GET'])
def profile():
    if not 'userName' in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'image' in request.files:
            image = request.files['image']
            filename = secure_filename(image.filename)
            image_data = image.read()
            setimg(f"UPDATE users SET img=(%s) WHERE username='{session['userName']}';", image_data)
        if 'password' in request.form:
            password=request.form['password']
            if password:
                if not ("'" in password) and len(password)>=5:
                    execute(f"UPDATE users SET password='{password}' WHERE username='{session['userName']}';")
                    flash('password is changed!')
                else:
                    flash("The length of the password is at least 5 characters, it is forbidden to use ' in order to protect against sql injections!")


    imgd=executeOne(f"SELECT img FROM users WHERE username='{session['userName']}';")[0]

    if imgd:
        return render_template('prof.html', session=session, img=True)
    return render_template('prof.html', session=session, img=False)




# get chat-avatar handler
@app.route('/get-image/<name>')
def get_image(name):

    image_data = executeOne(f"SELECT img FROM users WHERE username='{name}';")[0]

    if image_data:

        return send_file(
            BytesIO(image_data),
            mimetype='image/png'
        )
    else:
        image_data = executeOne(f"SELECT img FROM users WHERE username='empty';")[0]
        return send_file(
            BytesIO(image_data),
            mimetype='image/png'
        )



# profile deleting handler
@app.route('/delprof')
def delprof():
    if not 'userName' in session:
        return redirect(url_for('login'))
    s=session['userName']
    session.pop('userName', None)
    execute(f"DELETE FROM users WHERE username='{s}';")
    execute(f"DELETE FROM chats WHERE user1='{s}' OR user2='{s}';")
    l=executeAll(f"SELECT key FROM mess WHERE auth='{s}' OR get='{s}';")
    for i in l:
        execute(f"DELETE FROM images WHERE key='{i[0]}';")
    execute(f"DELETE FROM mess WHERE auth='{s}' OR get='{s}';")
    return redirect(url_for('index'))


# other user's profile page handler
@app.route('/otherprof/<username>')
def oprof(username):
    if not checkId(f"SELECT * FROM users WHERE username='{username}';"):
        return redirect(url_for('index'))
    if 'userName' in session:
        if username==session['userName']:
            return redirect(url_for('profile'))

    imgd = executeOne(f"SELECT img FROM users WHERE username='{username}';")[0]

    if imgd:
        return render_template('oprof.html', username=username, img=True, session=session)
    return render_template('oprof.html', username=username, img=False, session=session)



# group creating page
@app.route('/newgroup', methods=['POST', 'GET'])
def newgroup():
    if not 'userName' in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        name=request.form['group-name']
        if "'" in name or len(name)<3:
            flash("minimum name length is 3 characters, it is forbidden to use ' for SQL injections")
        else:
            if checkId(f"SELECT * FROM groups WHERE name='{name}';") or checkId(f"SELECT * FROM users WHERE username='{name}';"):
                flash('a group with this name already exists')
            else:
                execute(f"INSERT INTO groups (name, admin, members) VALUES ('{name}', '{session['userName']}', '_');")
                return redirect(url_for('group', gname=name))

    return render_template('newgroup.html')



# group chat page handler
@app.route('/group/<gname>', methods=['POST', 'GET'])
def group(gname):
    if not 'userName' in session:
        return redirect(url_for('login'))
    if not checkId(f"SELECT * FROM groups WHERE name='{gname}';"):
        return redirect(url_for('index'))
    memb = executeOne(f"SELECT members FROM groups WHERE name='{gname}';")[0]
    adm=executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]
    if not (session['userName'] in memb) and adm!=session['userName']:
        return redirect(url_for('index'))



    if request.method=='POST':
        text = request.form['text']
        if text != '':
            if "'" in text:
                flash("don't use ' for SQL injections!")
            else:
                execute(f"INSERT INTO mess (text, auth, get) VALUES ('{text}', '{session['userName']}', '{gname}');")

        elif 'image' in request.files:
            image = request.files['image']
            filename = secure_filename(image.filename)
            image_data = image.read()
            key = getRandomKey()
            execute(f"INSERT INTO mess (auth, get, key) VALUES ('{session['userName']}', '{gname}', '{key}');")
            setimg(f"INSERT INTO images (key, img) VALUES ('{key}', (%s))", image_data)

    adm=executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]
    mess=executeAll(f"SELECT * FROM mess WHERE get='{gname}';")
    return render_template('group.html', mess=mess, username=gname, admin=adm)


# adding user to group
@app.route('/adduser/<gname>',  methods=['POST', 'GET'])
def adduser(gname):
    if not 'userName' in session:
        return redirect(url_for('login'))
    if not checkId(f"SELECT * FROM groups WHERE name='{gname}';"):
        return redirect(url_for('index'))
    adm=executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]
    if adm!=session['userName']:
        return redirect(url_for('index'))
    if not (checkId(f"SELECT * FROM groups WHERE name='{gname}';")):
        return redirect(url_for('index'))
    if request.method=='POST':
        if not "'" in request.form['group-name']:
            memb=executeOne(f"SELECT members FROM groups WHERE name='{gname}';")[0]
            name = request.form['group-name']
            if not checkId(f"SELECT * FROM users WHERE username='{name}';"):
                flash("that user doesn't exist!")
            elif name in memb or name==executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]:
                flash("that user is already in group")
            else:
                memb+=f'_{name}'
                execute(f"UPDATE groups SET members='{memb}' WHERE name='{gname}';")
                return redirect(url_for('group', gname=gname))
        else:
            flash("don't use ' for SQL injections!")
    return render_template('adduser.html')




# function for go to chat with other user
@app.route('/gochat/<name>')
def gochat(name):
    if not 'userName' in session:
        return redirect(url_for('login'))

    if checkId(f"SELECT * FROM chats WHERE (user1='{name}' and user2='{session['userName']}') OR (user1='{session['userName']}' and user2='{name}');"):
        return redirect(url_for('chat', username=name))
    else:
        execute(f"INSERT INTO chats (user1, user2) VALUES ('{session['userName']}', '{name}');")
        return redirect(url_for('chat', username=name))


# message deleting
@app.route('/delmes/<text>/<auth>/<get>')
def delmes(text, auth, get):
    if not 'userName' in session:
        return redirect(url_for('index'))
    elif session['userName']!=auth:
        return redirect(url_for('index'))
    execute(f"DELETE FROM mess WHERE text='{text}' AND auth='{auth}' AND get='{get}';")
    if checkId(f"SELECT * FROM users WHERE username='{get}';"):
        return redirect(url_for('chat', username=get))
    else:
        return redirect(url_for('group', gname=get))



# message with image deleting
@app.route('/delimg/<auth>/<get>/<key>')
def delimg(auth, get, key):
    if not 'userName' in session:
        return redirect(url_for('index'))
    elif session['userName'] != auth:
        return redirect(url_for('index'))
    execute(f"DELETE FROM mess WHERE auth='{auth}' AND get='{get}' AND key='{key}';")
    execute(f"DELETE FROM images WHERE key='{key}';")
    if checkId(f"SELECT * FROM users WHERE username='{get}';"):
        return redirect(url_for('chat', username=get))
    else:
        return redirect(url_for('group', gname=get))




# deleting user from a group
@app.route('/delus/<gname>',  methods=['POST', 'GET'])
def delus(gname):
    if not 'userName' in session:
        return redirect(url_for('login'))
    if not checkId(f"SELECT * FROM groups WHERE name='{gname}';"):
        return redirect(url_for('index'))
    adm=executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]
    if adm!=session['userName']:
        return redirect(url_for('index'))
    if request.method=='POST':
        if "'" in request.form['group-name']:
            flash("don't use ' for SQL injections!")
        else:
            memb = executeOne(f"SELECT members FROM groups WHERE name='{gname}';")[0]
            if not(request.form['group-name'] in memb):
                flash("that user isn't in this group or he is the admin!")
            else:
                s='_'+request.form['group-name']
                memb=memb.replace(s, '')
                execute(f"UPDATE groups SET members='{memb}' WHERE name='{gname}';")
                return redirect(url_for('group', gname=gname))

    return render_template('delus.html')



# group deleting
@app.route('/delgroup/<gname>',  methods=['POST', 'GET'])
def delgroup(gname):
    if not 'userName' in session:
        return redirect(url_for('login'))
    if not checkId(f"SELECT * FROM groups WHERE name='{gname}';"):
        return redirect(url_for('index'))
    adm = executeOne(f"SELECT admin FROM groups WHERE name='{gname}';")[0]
    if adm!=session['userName']:
        return redirect(url_for('group', gname=gname))

    mss=executeAll(f"SELECT * FROM mess WHERE get='{gname}';")
    execute(f"DELETE FROM mess WHERE get='{gname}';")
    for i in mss:
        if i[3]:
            execute(f"DELETE FROM images WHERE key='{i[3]}';")
    execute(f"DELETE FROM groups WHERE name='{gname}';")
    return redirect(url_for('index'))





# incorrect url handler
@app.errorhandler(404)  # обработчик неверного URL
def pagenotfound(error):
    return render_template('error.html')







#
if __name__=="__main__":
    app.run(debug=True)