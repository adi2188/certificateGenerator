import unittest
import os
import csv
import shutil
from io import BytesIO

# Add project root to sys.path to allow importing certificate_generator.app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from certificate_generator.app import app, create_certificate

# Helper CSV Data
VALID_CSV_DATA_CONTENT = (
    "Person Name,Course Name,Course Description,Course Date\n"
    "Alice Smith,Python Programming,Learn Python basics,2023-01-15\n"
    "Bob Johnson,Advanced Web Development,Master front-end and back-end,2023-02-20\n"
)

CSV_MISSING_HEADER_CONTENT = (
    "Person Name,Course Description,Course Date\n" # Missing "Course Name"
    "Charlie Brown,Data Science Fundamentals,Introduction to ML,2023-03-10\n"
)

EMPTY_CSV_CONTENT = "Person Name,Course Name,Course Description,Course Date\n" # Headers only

CSV_WITH_EMPTY_ROW_CONTENT = (
    "Person Name,Course Name,Course Description,Course Date\n"
    "Eve Davis,Cybersecurity Basics,Intro to security,2023-05-01\n"
    ",,, \n" # Empty row (Person Name will be empty string, but app.py defaults to 'N/A' for message)
    "Frank Green,Cloud Computing,AWS and Azure,2023-06-10\n"
)


class TestCertificateGenerator(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms
        app.config['SECRET_KEY'] = 'test_secret_key' # Set a secret key for session/flashing
        self.client = app.test_client()

        # Define test-specific paths
        self.test_dir = os.path.dirname(__file__)
        self.original_upload_folder = app.config['UPLOAD_FOLDER']
        self.original_generated_pdfs_folder = app.config['GENERATED_PDFS_FOLDER']

        self.test_uploads_folder = os.path.join(self.test_dir, 'test_uploads')
        self.test_generated_pdfs_folder = os.path.join(self.test_dir, 'test_generated_pdfs')

        # Override app config
        app.config['UPLOAD_FOLDER'] = self.test_uploads_folder
        app.config['GENERATED_PDFS_FOLDER'] = self.test_generated_pdfs_folder
        
        # Create test directories
        os.makedirs(self.test_uploads_folder, exist_ok=True)
        os.makedirs(self.test_generated_pdfs_folder, exist_ok=True)

    def tearDown(self):
        # Remove test directories and their contents
        if os.path.exists(self.test_uploads_folder):
            shutil.rmtree(self.test_uploads_folder)
        if os.path.exists(self.test_generated_pdfs_folder):
            shutil.rmtree(self.test_generated_pdfs_folder)
        
        # Restore original config
        app.config['UPLOAD_FOLDER'] = self.original_upload_folder
        app.config['GENERATED_PDFS_FOLDER'] = self.original_generated_pdfs_folder


    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Upload CSV for Certificate Generation", response.data)

    def test_upload_no_file_selected(self):
        response = self.client.post('/upload', data={}, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b"No file part in the request. Please choose a CSV file.", response.data)

    def test_upload_empty_filename(self):
        data = {'csv_file': (BytesIO(b""), '')} # Empty filename
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No file selected. Please choose a CSV file.", response.data)

    def test_upload_invalid_file_type(self):
        data = {'csv_file': (BytesIO(b"this is not a csv"), 'test.txt')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True) 
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b"Invalid file type. Please upload a .csv file.", response.data)

    def test_upload_valid_csv_and_pdf_generation(self):
        data = {'csv_file': (BytesIO(VALID_CSV_DATA_CONTENT.encode('utf-8')), 'valid_data.csv')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Successfully generated all certificates!", response.data) 
        self.assertIn(b"Processed 2 rows.", response.data) 
        self.assertIn(b"AS-PythonProgramming-150123.pdf", response.data)
        self.assertIn(b"BJ-AdvancedWebDevelopment-200223.pdf", response.data)

        generated_files = os.listdir(self.test_generated_pdfs_folder)
        self.assertEqual(len(generated_files), 2)
        self.assertIn("AS-PythonProgramming-150123.pdf", generated_files)
        self.assertIn("BJ-AdvancedWebDevelopment-200223.pdf", generated_files)

    def test_upload_csv_missing_headers(self):
        data = {'csv_file': (BytesIO(CSV_MISSING_HEADER_CONTENT.encode('utf-8')), 'missing_headers.csv')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200) 
        self.assertIn(b"CSV file is missing required columns: Course Name", response.data)
        
        generated_files = os.listdir(self.test_generated_pdfs_folder)
        self.assertEqual(len(generated_files), 0)

    def test_upload_empty_csv_file(self):
        data = {'csv_file': (BytesIO(EMPTY_CSV_CONTENT.encode('utf-8')), 'empty.csv')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CSV file is empty or could not be parsed.", response.data)
        generated_files = os.listdir(self.test_generated_pdfs_folder)
        self.assertEqual(len(generated_files), 0)

    def test_upload_csv_with_empty_row(self):
        data = {'csv_file': (BytesIO(CSV_WITH_EMPTY_ROW_CONTENT.encode('utf-8')), 'empty_row.csv')}
        response = self.client.post('/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully generated 2 PDF(s), but failed for 1 entries. See details below.', response.data)
        self.assertIn(b"Row 2 (Person: N/A) - Missing data", response.data) # Corrected this line
        
        generated_files = os.listdir(self.test_generated_pdfs_folder)
        self.assertEqual(len(generated_files), 2)
        self.assertIn("ED-CybersecurityBasics-010523.pdf", generated_files)
        self.assertIn("FG-CloudComputing-100623.pdf", generated_files)


    def test_create_certificate_function(self):
        test_output_filename = "Test_User_Test_Course_certificate.pdf"
        test_output_path = os.path.join(self.test_generated_pdfs_folder, test_output_filename)
        
        create_certificate("Test User", "Test Course", "A comprehensive test course.", "2023-10-26", test_output_path)
        
        self.assertTrue(os.path.exists(test_output_path))
        self.assertTrue(os.path.getsize(test_output_path) > 0) 

if __name__ == '__main__':
    unittest.main()
