This README provides an overview of a Flask-based Python application designed to extract text from images, process the extracted text, and send it to a machine learning server. The application is equipped to schedule regular image processing tasks and store the extracted data in a PostgreSQL database.

Prerequisites:
    
    Before running this application, ensure you have the following prerequisites installed:
        
        Python 3.x
        Flask
        Pillow (Python Imaging Library)
        pytesseract (Tesseract OCR)
        SQLAlchemy
        Boto3 (Amazon Web Services SDK)
        Requests (HTTP library)
        PostgreSQL (with necessary configurations)
        Tesseract OCR installed and accessible in the system's PATH
        An active Wasabi S3 account with an S3 bucket configured

Installation:
    
    Clone the repository or download the source code.
    
    Install the required Python packages using pip:
        pip install flask pillow pytesseract sqlalchemy boto3 requests
    
    Ensure that Tesseract OCR is installed on your system. You can download it from https://github.com/tesseract-ocr/tesseract.

    Replace the following placeholders in the code with your own credentials:
        WASABI_ACCESS_KEY and WASABI_SECRET_KEY with your Wasabi S3 access keys.
        WASABI_BUCKET_NAME with the name of your Wasabi S3 bucket.
        Database connection parameters in the engine variable with your PostgreSQL database connection string.

Usage:

    Run the application by executing the following command in your terminal:

        python app.py
    
    The Flask application will start, and you will see output indicating that it is running.

    The application will automatically schedule tasks to process images located in the Wasabi S3 bucket and send the extracted data to a machine learning server. The scheduled tasks run every 1 Minute.

    You can access the application by navigating to http://127.0.0.1:5000/ in your web browser. It will return a "Hello, Flask!" message.

Application Structure:

    The application consists of the following components:

        Flask Web Application: This is the main application that handles HTTP requests, scheduling, and image processing.

        Tesseract OCR: Used to extract text from images.

        PostgreSQL Database: Stores the extracted data in a table called img_data.

        Wasabi S3: Serves as the storage for images to be processed.

        Machine Learning Server: The application sends extracted data to this server for further processing.

Endpoints:

    The Flask application has the following endpoints:

    /: Returns a simple "Hello, Flask!" message.

    /upload_image: Handles the image processing and data extraction. It also sends the extracted data to a machine learning server.

Scheduled Tasks:

    The application uses the schedule library to schedule tasks that run the /upload_image endpoint every 1 minute. This enables automatic processing of images in the Wasabi S3 bucket.

Database:

    The application uses PostgreSQL to store the extracted data. It creates a table called img_data with columns img_name (image filename) and extracted_text (the processed text). Data is inserted into this table after text extraction.

Error Handling:

    The application includes basic error handling for scenarios where text extraction fails or when there are no images to process. Error messages are returned as JSON responses.

License:

    This Flask Text Extraction and Processing Application is licensed under the MIT License. See the LICENSE file for details.