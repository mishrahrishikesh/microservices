from flask import Flask, jsonify, request
from mysql.connector import pooling
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_restx import Api, Resource, fields
import os
import bcrypt
from datetime import timedelta
 
app = Flask(__name__)

api= Api(app, doc='/docs/', version='1.0', title='Flask API with Swagger', description='A simple API for post and comment management.')
ns = api.namespace('blog', description='Blog to post and comment')

app.config["JWT_VERIFY_SUB"]= False #Disable subject verification
app.config["JWT_SECRET_KEY"] = "your_secret_key_here" #Set secret for app
app.config["JWT_ACCESS_TOKEN_EXPIRE"] = timedelta(minutes=30) #To set the token expiry

jwt = JWTManager(app) #intialize the JWT functionality in app

# Create a pool of connections to use anytime and return back when done
def get_db_connection():
    pool = pooling.MySQLConnectionPool(
        pool_name="connections",
        pool_size=5, #Number of connections to keep in the pool
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB")
    )
    return pool.get_connection()

user_Model = api.model('User', {
    'username': fields.String(required=True, description='The username of the user'),
    'password': fields.String(required=True, description='The password of the user'),
    'email': fields.String(required=True, description='The email of the user')
})

post_Model = api.model('Post', {
    'title': fields.String(required=True, description='The title of the post'),
    'content': fields.String(required=True, description='This is the content of the post')
})

comment_Model = api.model('Comment', {
    'content': fields.String(required=True, description='Content of the comment'),
    'post_id': fields.Integer(required=True, description='Post ID where comment will add')
})

# Function to create table in the database
def create_table():
    connection=get_db_connection()   # Borrow a connection from the pool
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            post_id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            comment_id INT AUTO_INCREMENT PRIMARY KEY,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INT,
            post_id INT,
            FOREIGN KEY(user_id) REFERENCES users(user_id),
            FOREIGN KEY(post_id) REFERENCES posts(post_id)
        )
    ''')
    connection.commit()
    cursor.close()
    connection.close()               # Return the connection to the pool
    print("Table created successfully!")

# Create the table when the app starts
create_table()

# Route for New User Registeration
#@app.route('/register', methods=['POST'])
@api.route('/register')
class Register(Resource):
    @api.expect(user_Model)
    def post(self):
        userData=request.get_json()
        username=userData.get('username')
        password=userData.get('password')
        email=userData.get('email')
        
        if not username or not password or not email:
            return jsonify({"error":"Please provide username, password, and email"})
        
        hashpass=bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        
        connection=get_db_connection()
        cur=connection.cursor()
        cur.execute('INSERT INTO users (username, password, email) VALUES(%s, %s, %s)',(username, hashpass.decode(), email))
        connection.commit()
        cur.close()
        connection.close()
        
        return jsonify({"message":"User registered successfully"})

#@app.route('/login', methods=['POST'])
@api.route('/login')
class Login(Resource):
    @api.expect(user_Model)
    def post(self):
        loginData=request.get_json()
        username=loginData.get('username')   
        password=loginData.get('password') 
        
        connection=get_db_connection()
        cur=connection.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user=cur.fetchone()
        
        if not user:
            return jsonify({"error": "Invalid username or password"})
        
        if not bcrypt.checkpw(password.encode(), user[2].encode()):
            return jsonify({"error": "Invalide username or password"})
        
        access_token = create_access_token(identity=user[0])
        cur.close()
        connection.close()
        # return jsonify({"message": "Login Successful!", "access_token": access_token}), 200
        return jsonify({"message":"Login Successful!", "access_token": access_token})
        
# Route to create a new post
#@app.route('/addPost', methods=['POST'])
@api.route('/addPost')
class AddPost(Resource):
    @api.expect(post_Model)
    @jwt_required()
    def post(self):
        postData = request.get_json()  # Getting the data in JSON format
        title = postData.get('title')
        content = postData.get('content')
        user_id = get_jwt_identity()
        
        if not title or not content:
            return jsonify({'error': 'title and content are required'})
        
        connection=get_db_connection()      # Borrow a connection from the pool
        cursor = connection.cursor()
        cursor.execute("INSERT INTO posts (title, content, user_id) VALUES (%s, %s, %s)", (title, content, user_id))
        connection.commit()
        cursor.close()
        connection.close()                   # Return the connection to the pool
        
        postDetails = {'title': title, 'content': content, 'user_id': user_id}
        return jsonify({'message': 'Post created', 'post': postDetails})

#@app.route("/addComment", methods=['POST'])
@api.route('/addComment')
class AddComment(Resource):
    @api.expect(comment_Model)
    @jwt_required()
    def post(self):
        commentData=request.get_json()
        content=commentData.get('content')
        user_id = get_jwt_identity()
        post_id=commentData.get('post_id')
        
        if not content or not user_id or not post_id:
            return jsonify({"error":'content, user_id, and post_id are required'})
        
        connection=get_db_connection()
        cur=connection.cursor()
        cur.execute('INSERT INTO comments (content, user_id, post_id) VALUES (%s, %s, %s)',(content, user_id, post_id))
        connection.commit()
        cur.close()
        connection.close()
        
        commentDetails={'content': content, 'user_id': user_id, 'post_id': post_id}
        return jsonify({"message":"Comment added successfully", 'comment': commentDetails})

#Show all users detailes
#@app.route('/users', methods=['GET'])
@api.route('/users')
class Users(Resource):
    def get(self):
        connection=get_db_connection()
        cur=connection.cursor()
        cur.execute('SELECT * FROM users')
        users_data=cur.fetchall()
        cur.close()
        connection.close()
        
        if not users_data:
            return jsonify({"error": "No users found!"})
        
        users=[{'user_id':user[0], 'username': user[1], 'email': user[3]} for user in users_data]
        return jsonify({'Users':users})

# Route to fetch all posts
#@app.route('/posts', methods=['GET'])
@api.route('/posts')
class Posts(Resource):
    def get(self):
        connection=get_db_connection()       # Borrow a connection from the pool
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM posts")
        posts_data = cursor.fetchall()
        cursor.close()
        connection.close()                   # Return the connection to the pool

        if not posts_data:
            return jsonify({'error': 'No posts available'})

        posts = [{'post_id': post[0], 'title': post[1], 'content': post[2], 'timestamp': post[3], 'user_id': post[4]} for post in posts_data]
        return jsonify({'posts': posts})

# @app.route('/posts/<int:user_id>', methods=['GET'])
@api.route('/posts/<int:user_id>')
class UserPost(Resource):
    def get(self, user_id):
        connection=get_db_connection()       # Borrow a connection from the pool
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM posts WHERE user_id = %s', (user_id,))
        posts_data = cursor.fetchall()
        cursor.close()
        connection.close()                   # Return the connection to the pool

        if not posts_data:
            return jsonify({'error': 'No posts available for this user id'})

        posts = [{'post_id': post[0], 'title': post[1], 'content': post[2], 'timestamp': post[3], 'user_id': post[4]} for post in posts_data]
        return jsonify({'posts': posts})

#Get comment of specific post
# @app.route('/comments/<int:post_id>', methods=['GET'])
@api.route('/comments/<int:post_id>')
class PostComment(Resource):
    def showComments(self, post_id):
        connection=get_db_connection()
        cur=connection.cursor()
        cur.execute('SELECT * FROM comments WHERE post_id = %s', (post_id,))
        comments_data=cur.fetchall()
        cur.close()
        connection.close()
        
        if not comments_data:
            return jsonify({"error": "No comments available for this post"})
        
        comments=[{'comment_id': comment[0], 'content': comment[1], 'timestamp': comment[2], 'user_id': comment[3], 'post_id': comment[4]} for comment in comments_data]
        return jsonify({"comments": comments}), 200

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)