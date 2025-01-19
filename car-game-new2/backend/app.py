from flask import Flask, jsonify, request
import mysql.connector
import os

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DATABASE_HOST', 'localhost'),
        user=os.getenv('DATABASE_USER', 'root'),
        password=os.getenv('DATABASE_PASSWORD', 'password'),
        database=os.getenv('DATABASE_NAME', 'game_db')
    )
    return conn

# Create table if it doesn't exist
def create_table_if_not_exists():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure the 'data' table exists for message
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS data (
        id INT AUTO_INCREMENT PRIMARY KEY,
        message VARCHAR(255)
    );
    """)
    
    # Create the 'scores' table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scores (
        id INT AUTO_INCREMENT PRIMARY KEY,
        score INT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Save score to the database
@app.route('/save_score', methods=['POST'])
def save_score():
    data = request.get_json()
    score = data.get('score')

    if score is None:
        return jsonify({'error': 'Missing score'}), 400

    # Insert the score into the database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert new score into the table
    cursor.execute("""
    INSERT INTO scores (score)
    VALUES (%s);
    """, (score,))
    
    conn.commit()

    # Check if the new score is a high score and update it
    cursor.execute("SELECT MAX(score) FROM scores")
    high_score = cursor.fetchone()
    
    cursor.close()
    conn.close()

    return jsonify({'message': 'Score saved successfully', 'high_score': high_score[0]}), 200

# Route to get the highest score
@app.route('/high_score', methods=['GET'])
def high_score():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(score) FROM scores")
    high_score = cursor.fetchone()
    
    cursor.close()
    conn.close()

    return jsonify({'high_score': high_score[0] if high_score[0] is not None else 0})

# Main route to get a welcome message
@app.route('/')
@app.route('/data', methods=['GET'])
def get_data():
    try:
        create_table_if_not_exists()  # Ensure the table exists before querying
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Retrieve the welcome message
        cursor.execute("SELECT message FROM data LIMIT 1")
        message = cursor.fetchone()

        # Fetch the highest score from the scores table
        cursor.execute("SELECT MAX(score) FROM scores")
        high_score = cursor.fetchone()

        cursor.close()
        conn.close()

        if message and high_score:
            return jsonify({
                'message': message[0],
                'high_score': high_score[0] if high_score[0] is not None else 0
            })
        else:
            return jsonify({'message': 'No data available'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
