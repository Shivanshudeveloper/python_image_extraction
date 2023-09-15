from flask import Flask, request, jsonify
import requests
import pytesseract  
from PIL import Image
import threading
import re
import boto3
import os
import schedule
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker  # Import sessionmaker
from dotenv import load_dotenv
load_dotenv()
# Access the environment variables using the Config object
WASABI_ACCESS_KEY = os.getenv('WASABI_ACCESS_KEY')
WASABI_SECRET_KEY = os.getenv('WASABI_SECRET_KEY')
WASABI_BUCKET_NAME = os.getenv('WASABI_BUCKET_NAME')

# engine = create_engine('postgres://tsdbadmin:hm87vy2trrbags36@nt51y7xqhs.knrrchtp81.tsdb.cloud.timescale.com:36489/tsdb')
engine = create_engine(os.getenv('POSTGRES_URI'))

app = Flask(__name__)
scheduler_started = False


s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('S3_ENDPOINT'),  # Wasabi S3 endpoint
    aws_access_key_id=WASABI_ACCESS_KEY,
    aws_secret_access_key=WASABI_SECRET_KEY
)

Session = sessionmaker(bind=engine)

screenshots_folder = os.path.join(os.getcwd(), 'screenshots')
os.makedirs(screenshots_folder, exist_ok=True)

def start_scheduler():
    global scheduler_started
    if not scheduler_started:
        # Schedule the job to run the upload_image route every 10 seconds
        schedule.every(10).seconds.do(lambda: app.test_client().post('/upload_image'))
        
        # Run the scheduled jobs in the background
        while True:
            schedule.run_pending()
            time.sleep(1)

def create_img_data_table():
    # Create a new session
    session = Session()
    try:
        # Define the SQL query to create the img_data table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS img_data (
            img_name VARCHAR(255),
            extracted_text TEXT
        )
        """
        
        # Execute the query to create the table
        session.execute(text(create_table_query))
        
        # Commit the changes to the database
        session.commit()
    except Exception as e:
        # Roll back the transaction if an error occurs
        session.rollback()
        raise e
    finally:
        # Close the session
        session.close()

def insert_img_data(img_name, extracted_text):
    # Create a new session
    session = Session()
    try:
        # Define the SQL query to insert data into the table
        insert_query = text("INSERT INTO img_data (img_name, extracted_text) VALUES (:img_name, :extracted_text)")
        
        # Execute the query with the provided parameters
        session.execute(insert_query, {"img_name": img_name, "extracted_text": extracted_text})
        
        # Commit the changes to the database
        session.commit()
        print("data inserted successfully")
    except Exception as e:
        # Roll back the transaction if an error occurs
        session.rollback()
        raise e
    finally:
        # Close the session
        session.close()

def extract_person_names_and_titles(text):
    # Define a regular expression pattern to match person names and titles
    pattern = r'([A-Z][a-zA-Z]+(?: [A-Z][a-zA-Z]*)*)'

    # Find all matches in the text
    matches = re.findall(pattern, text)

    # Remove duplicates by converting the matches to a set and then back to a list
    unique_matches = list(set(matches))

    return unique_matches

def remove_unwanted_words(text):
    # Define a list of unwanted words
    unwanted_words = [
        'me', 'the', 'and', 'or', 'a', 'an', 'is', 'in', 'on', 'at', 'how', 'to', 'connect', 'setup',
        'an', 'introduction', 'transfer', 'money', 'over', 'upgrading', 'search', 'with', 'for', 'as',
        'up', 'off', 'be', 'by', 'of', 'it', 'its', 'from', 'when', 'where', 'which', 'who', 'whom', 'whose'
    ]

    # Split the text into words
    words = text.split()

    # Remove unwanted words from the list of words
    clean_words = [word for word in words if word.lower() not in unwanted_words]

    # Join the clean words back into a cleaned text
    cleaned_text = ' '.join(clean_words)

    return cleaned_text

def normalize_text(text):
    # Convert the text to lowercase and remove leading/trailing spaces
    normalized_text = text.lower().strip()

    return normalized_text

def read_text_from_image(image_path):
    try:
        # Open the image using Pillow
        image = Image.open(image_path)
        
        # Extract text using Tesseract OCR
        extracted_text = pytesseract.image_to_string(image)
        return extracted_text
    except Exception as e:
        print("Error:", str(e))
        return None
    
def remove_short_strings(array):
    # Use a list comprehension to filter out strings with length <= 2
    filtered_array = [string for string in array if len(string) > 2]

    return filtered_array

def remove_short_words(input_string):
    # Split the input string into words
    words = input_string.split()

    # Use a list comprehension to filter out words with length <= 2
    filtered_words = [word for word in words if len(word) > 2]

    # Join the filtered words back into a string
    result_string = ' '.join(filtered_words)

    return result_string


def extract_words_to_array(input_string):
    # Define a regular expression pattern to match words
    pattern = r'\b\w+\b'

    # Find all matches in the input string
    words = re.findall(pattern, input_string)

    return words

def remove_unwanted_words_from_array(input_array):
    # Define a regular expression pattern to match unwanted words
    unwanted_pattern = r'\b(?:\w*\d\w*|[\d.]+)\b'

    # Use list comprehension to filter out unwanted words from the array
    cleaned_array = [re.sub(unwanted_pattern, '', word) for word in input_array]

    # Filter out empty strings from the cleaned array
    cleaned_array = list(filter(None, cleaned_array))

    return cleaned_array

@app.route('/')
def hello():
    return 'Hello, Flask!'


@app.route('/upload_image', methods=['POST'])
def upload_image():
    # Create a session
    session = Session()

    query = text("SELECT img_name FROM img_info WHERE status = 'false' LIMIT 1")
    result = session.execute(query)
    row = result.fetchone()

    if row:
        img_name = row[0]
        image_path = f'screenshots/{img_name}'  # Adjust the path structure as needed

        # Download the image from Wasabi
        response = s3_client.get_object(Bucket=WASABI_BUCKET_NAME, Key=image_path)
        image_data = response['Body'].read()
        local_image_path = os.path.join(screenshots_folder, f'{img_name}.png')
        with open(local_image_path, 'wb') as image_file:
            image_file.write(image_data)
        # Update the status of the fetched img_name to "true" (assuming you want to mark it as processed)
        update_query = text("UPDATE img_info SET status = 'true' WHERE img_name = :img_name")
        session.execute(update_query, params={"img_name": img_name})  # Use params to pass parameters
        session.commit()  # Commit the transaction
        session.close()

        # return jsonify({'img_name': img_name}), 200
    else:
        session.close()  # Close the session
        # return jsonify({'error': 'No img_name with status="false" found.'}), 404

    # Perform any processing with the image file here, such as saving it to disk or processing the image data

    try:
        # Extract text from the image
        extracted_text = read_text_from_image(local_image_path)
        if extracted_text:
            # Extract person names and titles
            names_and_titles = extract_person_names_and_titles(extracted_text)

            # Call the function to remove short strings
            clean_names_and_titles_array = remove_short_strings(names_and_titles)


            # Remove unwanted words from the text
            cleaned_text = remove_unwanted_words(extracted_text)
            # Normalize the text
            normalized_text = normalize_text(cleaned_text)

            # Call the function to remove short words
            clean_normalized_text = remove_short_words(normalized_text)

            # Call the function to extract words to an array
            words_array = extract_words_to_array(clean_normalized_text)

            # Call the function to remove short strings
            short_words_array = remove_short_strings(words_array)

            # Call the function to remove unwanted words
            clean_words_array = remove_unwanted_words_from_array(short_words_array)
            final_string = " ".join(clean_words_array)
            print("Successfully got the text",final_string)
            response_data = {
                    'img_name': img_name,
                    'extracted_text':final_string
                }
            # insert_img_data(img_name,final_string)
                # Return a JSON response with the extracted data
            # return jsonify(response_data), 200
            # Define the URL of the server to send the POST request
            server_url = 'http://127.0.0.1:8080/mlwork'

            try:
                # Send the array as a JSON payload in the POST request
                response = requests.post(server_url, json={"userData": clean_names_and_titles_array, "userId":img_name})

                # Check the response from the server
                if response.status_code == 200:
                    result = response.json()
                    return jsonify(result), 200
                else:
                    return jsonify({'error': 'Server error.'}), 500

            except requests.exceptions.RequestException as e:
                return jsonify({'error': f'Request failed: {e}'}), 500

            # return jsonify({'userData': clean_names_and_titles_array}), 200

        else:
            print(f"No text could be extracted from")
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': 'Text extraction failed.'}), 500


if __name__ == '__main__':
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True  # This allows the thread to exit when the main program exits
    scheduler_thread.start()
    app.run(debug=True)