# app.py

import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
import spacy

# Load environment variables
load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable not found.")

# Configure the Gemini API
genai.configure(api_key=api_key)

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Path to the manuals directory
MANUALS_DIR = os.path.join(os.getcwd(), 'manuals')
os.makedirs(MANUALS_DIR, exist_ok=True)

# Allowed file extensions for manual uploads
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to extract content from a PDF
def extract_manual_content(filepath):
    content = ""
    try:
        import PyPDF2
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                content += page.extract_text()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return content

# Load manuals into memory
MANUALS = {}
manual_names = ["Arista_EOS", "Cisco_IOS"]
for manual_name in manual_names:
    filepath = os.path.join(MANUALS_DIR, f"{manual_name}.pdf")
    if os.path.exists(filepath):
        MANUALS[manual_name] = extract_manual_content(filepath)
    else:
        print(f"Manual not found: {filepath}")

# Function to find the relevant manual based on the input data
def find_relevant_manual(data):
    data_lower = data.lower()
    for manual_name in MANUALS.keys():
        if manual_name.lower() in data_lower:
            return manual_name, MANUALS[manual_name]
    return None, None

# Endpoint to upload manuals
@app.route('/upload_manual', methods=['POST'])
def upload_manual():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(MANUALS_DIR, filename))
        return jsonify({'message': f'File {filename} uploaded successfully'}), 201
    else:
        return jsonify({'error': 'File type not allowed'}), 400

# Endpoint to list manuals
@app.route('/list_manuals', methods=['GET'])
def list_manuals():
    files = os.listdir(MANUALS_DIR)
    return jsonify({'manuals': files}), 200

# Endpoint to download a manual
@app.route('/download_manual/<filename>', methods=['GET'])
def download_manual(filename):
    try:
        return send_from_directory(MANUALS_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404

# Endpoint to process a manual
@app.route('/process_manual/<filename>', methods=['POST'])
def process_manual(filename):
    file_path = os.path.join(MANUALS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    # Process the manual based on file extension
    file_extension = filename.rsplit('.', 1)[1].lower()

    if file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    elif file_extension == 'pdf':
        # Use PyPDF2 to read PDF files
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
    elif file_extension == 'docx':
        # Use python-docx to read DOCX files
        import docx
        doc = docx.Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
    else:
        return jsonify({'error': 'Unsupported file type for processing'}), 400

    # Process text with spaCy
    doc = nlp(text)
    # Implement your parsing logic here
    # For example, extract commands or configurations
    commands = [ent.text for ent in doc.ents if ent.label_ == 'COMMAND']

    # Return extracted commands or other data
    return jsonify({'commands': commands}), 200

# Endpoint to classify an error message using Gemini 1.5 API
@app.route('/classify_error', methods=['POST'])
def classify_error():
    data = request.get_json()
    if not data or 'error_message' not in data:
        return jsonify({'error': 'No error message provided'}), 400

    error_message = data['error_message'].strip()
    if not error_message:
        return jsonify({'error': 'Empty error message provided'}), 400

    try:
        # Find the relevant manual
        manual_name, manual_content = find_relevant_manual(error_message)
        if manual_name and manual_content:
            # Limit the manual content to a reasonable length
            MAX_MANUAL_CONTENT_LENGTH = 500  # Adjust as needed
            manual_excerpt = manual_content[:MAX_MANUAL_CONTENT_LENGTH]
            manual_excerpt = manual_excerpt.strip()
        else:
            manual_excerpt = "No relevant manual is available for this issue."

        # Prepare the prompt
        prompt = (
            f"Please provide troubleshooting steps for the following network error. "
            f"Your response should be in the following format:\n\n"
            f"Here is what the manual says:\n"
            f"\"[Insert relevant manual-like explanation]\"\n\n"
            f"Here are some tips on the issue:\n"
            f"[AI-generated tips or recommendations]\n\n"
            f"Network error:\n{error_message}\n\n"
            f"Relevant manual content:\n{manual_excerpt}\n\n"
            f"Please ensure your response follows the format exactly, even if no manual is available."
        )
        print(f"Prompt sent to Gemini API: {prompt}")

        # Initialize the Gemini API model
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception as e:
            print(f"Error initializing Gemini Model: {e}")
            return jsonify({'error': 'Failed to initialize Gemini API model', 'details': str(e)}), 500

        # Call the API
        try:
            response = model.generate_content(prompt)
            print(f"Gemini API response: {response}")
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("Unexpected API response structure or empty response.")

            ai_response = response.text.strip()

            # Parse the AI response into the two sections
            # Split the response based on the headings
            manual_section = ""
            tips_section = ""

            if "Here are some tips on the issue:" in ai_response:
                parts = ai_response.split("Here are some tips on the issue:")
                manual_part = parts[0].replace("Here is what the manual says:", "").strip()
                tips_part = parts[1].strip()
                manual_section = manual_part.strip('"').strip()
                tips_section = tips_part
            else:
                # If the format is not as expected, return the whole response in tips_section
                tips_section = ai_response

        except Exception as e:
            print(f"Error processing Gemini API response: {e}")
            return jsonify({'error': 'Failed to process API response', 'details': str(e)}), 500

        # Prepare the response
        response_data = {
            'manual_response': manual_section,
            'tips_response': tips_section,
        }
        if manual_name:
            response_data['manual_used'] = manual_name

        return jsonify(response_data), 200
    except Exception as e:
        print(f"Unexpected error in /classify_error: {e}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500







# Endpoint to translate commands between systems
@app.route('/translate_command', methods=['POST'])
def translate_command():
    data = request.get_json()
    source_system = data.get('source_system')
    target_system = data.get('target_system')
    source_command = data.get('source_command')

    if not all([source_system, target_system, source_command]):
        print(f"Invalid request data: {data}")
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Initialize the Gemini API model
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception as e:
            print(f"Error initializing Gemini Model: {e}")
            return jsonify({'error': 'Failed to initialize Gemini API model', 'details': str(e)}), 500

        # Prepare the prompt
        prompt = (
            f"Translate the following network command from {source_system} to {target_system}:\n\n"
            f"{source_command}"
        )
        print(f"Prompt sent to Gemini API: {prompt}")

        # Call the API
        try:
            response = model.generate_content(prompt)
            print(f"Gemini API response: {response}")
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("Unexpected API response structure or empty response.")
            translated_command = response.text.strip()
        except Exception as e:
            print(f"Error processing Gemini API response: {e}")
            return jsonify({'error': 'Failed to process API response', 'details': str(e)}), 500

        return jsonify({'translated_command': translated_command}), 200
    except Exception as e:
        print(f"Unexpected error in /translate_command: {e}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

# Endpoint to generate configuration based on input
@app.route('/generate_config', methods=['POST'])
def generate_config():
    data = request.get_json()
    # Extract necessary parameters from data
    interface = data.get('interface')
    ip_address = data.get('ip_address')
    subnet_mask = data.get('subnet_mask')

    if not all([interface, ip_address, subnet_mask]):
        return jsonify({'error': 'Missing required configuration parameters'}), 400

    try:
        # Initialize the Gemini API model
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception as e:
            print(f"Error initializing Gemini Model: {e}")
            return jsonify({'error': 'Failed to initialize Gemini API model', 'details': str(e)}), 500

        # Prepare the prompt
        prompt = (
            f"Generate a network configuration for interface {interface} "
            f"with IP address {ip_address} and subnet mask {subnet_mask}."
        )
        print(f"Prompt sent to Gemini API: {prompt}")

        # Call the API
        try:
            response = model.generate_content(prompt)
            print(f"Gemini API response: {response}")
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("Unexpected API response structure or empty response.")
            configuration = response.text.strip()
        except Exception as e:
            print(f"Error processing Gemini API response: {e}")
            return jsonify({'error': 'Failed to generate configuration', 'details': str(e)}), 500

        return jsonify({'configuration': configuration}), 200
    except Exception as e:
        print(f"Unexpected error in /generate_config: {e}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

# Endpoint to format command into XML
@app.route('/format_xml', methods=['POST'])
def format_xml():
    data = request.get_json()
    command = data.get('command')

    if not command:
        return jsonify({'error': 'No command provided'}), 400

    try:
        # Initialize the Gemini API model
        try:
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        except Exception as e:
            print(f"Error initializing Gemini Model: {e}")
            return jsonify({'error': 'Failed to initialize Gemini API model', 'details': str(e)}), 500

        # Prepare the prompt
        prompt = f"Convert the following network command into XML format:\n\n{command}"
        print(f"Prompt sent to Gemini API: {prompt}")

        # Call the API
        try:
            response = model.generate_content(prompt)
            print(f"Gemini API response: {response}")
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("Unexpected API response structure or empty response.")
            xml_command = response.text.strip()
        except Exception as e:
            print(f"Error processing Gemini API response: {e}")
            return jsonify({'error': 'Failed to convert command to XML', 'details': str(e)}), 500

        return jsonify({'xml_command': xml_command}), 200
    except Exception as e:
        print(f"Unexpected error in /format_xml: {e}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
