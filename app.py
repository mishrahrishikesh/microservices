from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample data (you can replace this with a database in a real app)
posts = []

# POST route to create a new post
@app.route('/posts', methods=['POST'])
def create_post():
    data = request.get_json()  # Get JSON data from the request
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Title and content are required'}), 400

    # Create the post and append it to the posts list
    post = {'title': title, 'content': content}
    posts.append(post)

    return jsonify({'message': 'Post created', 'post': post}), 201

# GET route to retrieve all posts
@app.route('/posts', methods=['GET'])
def get_posts():
    if len(posts) == 0:
        return jsonify({'error': 'No posts available'}), 404
    return jsonify({"posts": posts}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, ssl_context=('ssl-certs/server.crt', 'ssl-certs/server.key'))

