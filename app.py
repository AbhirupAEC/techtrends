import sqlite3
import logging
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

#conatins db conn count
db_conn_counter = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_conn_counter
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_conn_counter=db_conn_counter+1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    global db_conn_counter
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    db_conn_counter=db_conn_counter-1
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


#returns post count
def get_post_count():
    global db_conn_counter
    connection = get_db_connection()
    cursor = connection.cursor()
    table_name = 'posts'
    query = f"SELECT COUNT(*) FROM {table_name}"
    cursor.execute(query)
    result = cursor.fetchone()
    post_count = result[0]
    connection.close()
    db_conn_counter=db_conn_counter-1
    return post_count

# Define the main route of the web application 
@app.route('/')
def index():
    global db_conn_counter
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    db_conn_counter=db_conn_counter-1
    return render_template('index.html', posts=posts)

#Provides health status
@app.route('/healthz')
def status():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    return response

@app.route('/metrics')
def metrics():
    global db_conn_counter
    response = app.response_class(
            response=json.dumps({"db_connection_count": db_conn_counter, "post_count": get_post_count()}),
            status=200,
            mimetype='application/json'
    )
    return response

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error("Info requested for non existing post")
      return render_template('404.html'), 404
    else:
      app.logger.info('Info retrieved for post '+str(post['title']))
      print(post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.debug('about page retreived')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    global db_conn_counter
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            app.logger.info('New post created')
            connection.close()
            db_conn_counter=db_conn_counter-1

            return redirect(url_for('index'))

    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
   logging.basicConfig(format="{asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",level=logging.DEBUG)
   app.run(host='0.0.0.0', port='3111')
