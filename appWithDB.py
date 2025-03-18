from flask import Flask, jsonify, request
from mysql.connector import pooling

app=Flask(__name__)

def get_db_connection():
    pool=pooling.MySQLConnectionPool(
        pool_name='mypool',
        pool_size=5,
        host='localhost',
        database='hrishi',
        username='root',
        password='root123'
    )
    return pool.get_connection()

def createTable():
    connection=get_db_connection()
    cur=connection.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id INT AUTO_INCREMENT PRIMARY KEY, title varchar(255), content text)')
    connection.commit()
    cur.close()
    connection.close()

createTable()

@app.route('/', methods=['POST'])
def post():
    data=request.get_json()
    title=data.get('title')
    content=data.get('content')
    if not title or not content:
        return jsonify({'error': 'title and content required'}), 400
    connection=get_db_connection()
    cur=connection.cursor()
    cur.execute('INSERT INTO posts(title, content) VALUES(%s, %s)', (title, content))
    post=({'title':title, 'content':content})
    connection.commit()
    cur.close()
    connection.close()
    return jsonify({'message':'post created successfully', 'post': post}), 201

@app.route('/', methods=['GET'])
def get():
    connection=get_db_connection()
    cur=connection.cursor()
    cur.execute('SELECT * FROM posts')
    posts=cur.fetchall()
    if not posts:
        return jsonify({'error': 'no post available'}), 400
    connection.commit()
    cur.close()
    connection.close()
    posts_data=[{'id': post[0], 'title':post[1], 'content':post[1]} for post in posts]
    return jsonify({'posts':posts_data}), 200
    
if __name__=='__main__':
    app.run(host='localhost', port=5001)