# user_input_page.py

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import PyPDF2  # For processing PDF files

# Import functions from api_calls.py
import api_calls

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    # Extract text from the uploaded PDF
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page in reader.pages:
                content += page.extract_text()
            return content
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

@app.route('/')
def index():
    return render_template('UI_markup.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Extract text from PDF
        content = extract_text_from_pdf(file_path)
        # You might want to process the content further or pass it to the frontend
        return jsonify({'message': 'File uploaded successfully', 'content': content})
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@app.route('/submit', methods=['POST'])
def submit_task():
    data = request.json
    rich_text = data.get('rich_text')
    # Get the OpenAI API key from environment variable
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key not found in environment variables'}), 500

    if not rich_text:
        return jsonify({'error': 'Rich-text instructions are required.'}), 400

    try:
        # Process instructions using api_calls module
        module_sequence = api_calls.process_instructions(
            input_text=rich_text,
            embedding_file='keyword_to_module.txt',  # Ensure this file is in the correct location
            api_key=openai_api_key
        )
        # Return the module sequence
        return jsonify({'module_sequence': module_sequence})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
