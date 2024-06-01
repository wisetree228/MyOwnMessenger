from flask import Flask, render_template, url_for, request, flash, get_flashed_messages, redirect, session, send_file, make_response, session
import psycopg2
import base64
from werkzeug.utils import secure_filename
from io import BytesIO

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




app=Flask(__name__)
app.secret_key='key123456789'

@app.route('/')
def index():

    links=[]

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



    return render_template('index.html', session=session, links=links)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username=request.form['username']
        password=request.form['password']
        if len(username)>=5 and len(password)>=5 and not("'" in username or "'" in password):
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


@app.route('/logout')
def logout():
    session.pop('userName', None)
    return redirect(url_for('index'))


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
            else:
                execute(f"INSERT INTO chats (user1, user2) VALUES ('{session['userName']}', '{name}');")
                return redirect(url_for('chat', username=name))
        else:
            flash("don't use ' for SQL injections!")
    return render_template('newchat.html')

@app.route('/chat/<username>', methods=['POST', 'GET'])
def chat(username):
    if not 'userName' in session:
        return redirect(url_for('index'))
    if not(checkId(f"SELECT * FROM chats WHERE user1='{session['userName']}' AND user2='{username}';") or checkId(f"SELECT * FROM chats WHERE user2='{session['userName']}' AND user1='{username}';")):
        return redirect('error')

    if username==session['userName']:
        return redirect('/error')

    if request.method=='POST':
        text=request.form['text']
        if "'" in text:
            flash("don't use ' for SQL injections!")
        else:
            execute(f"INSERT INTO mess (text, auth, get) VALUES ('{text}', '{session['userName']}', '{username}');")

    mess=executeAll(f"SELECT * FROM mess WHERE (auth='{session['userName']}' AND get='{username}') OR (auth='{username}' AND get='{session['userName']}')")

    return render_template('chat.html', mess=mess)





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
        #img_data_base64 = base64.b64encode(imgd).decode('utf-8')
        return render_template('prof.html', session=session, img=imgd)
    return render_template('prof.html', session=session, img=False)

@app.route('/get-image/<name>')
def get_image(name):
    # Получение изображения из базы данных
    image_data = executeOne(f"SELECT img FROM users WHERE username='{name}';")[0]

    if image_data:
        # Возвращение изображения в ответе Flask
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



@app.route('/delprof')
def delprof():
    if not 'userName' in session:
        return redirect(url_for('login'))
    s=session['userName']
    session.pop('userName', None)
    execute(f"DELETE FROM users WHERE username='{s}';")
    execute(f"DELETE FROM chats WHERE user1='{s}' OR user2='{s}';")
    execute(f"DELETE FROM mess WHERE auth='{s}' OR get='{s}';")
    return redirect(url_for('index'))






@app.errorhandler(404)  # обработчик неверного URL
def pagenotfound(error):
    return render_template('error.html')







#
if __name__=="__main__":
    app.run(debug=True)