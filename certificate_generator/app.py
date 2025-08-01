import os
import csv
import logging
import random
from datetime import datetime
from flask import Flask, request, current_app, render_template, url_for, send_from_directory, flash, redirect
from werkzeug.utils import secure_filename
from fpdf import FPDF
import json

app = Flask(__name__)
app.secret_key = 'your secret key' # Needed for flashing messages

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Configuration for upload and generated PDF folders
UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads')
GENERATED_PDFS_FOLDER = os.path.join(app.root_path, 'generated_pdfs')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_PDFS_FOLDER'] = GENERATED_PDFS_FOLDER

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GENERATED_PDFS_FOLDER'], exist_ok=True)

def generate_certificate_id(person_name, course_name, course_date):
    """Generates a unique certificate ID."""
    initials = "".join(part[0] for part in person_name.split()).upper()

    # Sanitize course name: remove newlines, then other non-alphanumeric chars, and shorten
    sanitized_course_name = course_name.replace("\n", " ").replace("\r", "")
    sanitized_course_name = "".join(filter(str.isalnum, sanitized_course_name))
    sanitized_course_name = sanitized_course_name[:8]

    # Use the first date from the date range for the ID
    first_date_str = course_date.split(':')[0]

    # Attempt to parse date from multiple formats
    date_obj = None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            date_obj = datetime.strptime(first_date_str, fmt)
            break
        except ValueError:
            pass

    if date_obj:
        date_str = date_obj.strftime('%d%m%y')
    else:
        # Fallback if date format is not as expected
        date_str = "000000"

    random_digits = f"{random.randint(0, 999999):06d}"

    return f"{initials}-{sanitized_course_name}-{date_str}-{random_digits}"

def create_certificate(person_name, course_name, course_description, course_date, certificate_id, output_path, instructor_pair):
    with open(os.path.join(app.root_path, 'config.json')) as f:
        config = json.load(f)

    pdf = FPDF()
    pdf.add_page()
    
    # Set background color
    pdf.set_fill_color(*config['background_color'])
    pdf.rect(0, 0, 210, 297, 'F')

    # Determine background image based on instructor pair
    image_mapping = {
        'DTK_RBB': 'static/DTK_RBB.jpg',
        'DTK_AA': 'static/DTK_AA.jpg'
    }
    background_image_name = image_mapping.get(instructor_pair, config.get('background_image', 'static/template.jpg'))
    background_image_path = os.path.join(app.root_path, background_image_name)

    if os.path.exists(background_image_path):
        pdf.image(background_image_path, x=0, y=0, w=210, h=297)

    # Header
    pdf.set_y(50)
    pdf.set_font(config['font_name'], 'BI', 20)
    pdf.set_text_color(*config['header_color'])
    pdf.cell(0, 10, config['header_text'], ln=True, align='C')

    # Certificate content
    pdf.set_y(config['course_name_y'])
    pdf.set_font(config['font_name'], "B", config['font_size_course_name'])
    pdf.set_text_color(0,0,0)
    pdf.multi_cell(0, 10, course_name, align="C")

    pdf.set_y(config['award_text_y'])
    pdf.set_font(config['font_name'], "", config['font_size_default'])
    pdf.cell(0, 10, "This certificate is awarded to:", ln=True, align="C")
    
    pdf.set_y(config['person_name_y'])
    pdf.set_font(config['font_name'], "B", config['font_size_person_name'])
    pdf.cell(0, 10, person_name, ln=True, align="C")
    
    pdf.set_y(config['completion_text_y'])
    pdf.set_font(config['font_name'], "", config['font_size_default'])
    pdf.cell(0, 10, "for successfully completing the course content:", ln=True, align="C")
    
    pdf.set_y(config['course_description_y'])
    pdf.set_font(config['font_name'], "I", config['font_size_default'])
    bulleted_description = "\n".join([f"* {line}" for line in course_description.splitlines()])
    pdf.multi_cell(0, 10, bulleted_description, align="C")
    
    pdf.set_y(config['date_y'])
    pdf.set_font(config['font_name'], "", config['font_size_default'])
    pdf.cell(0, 10, f"Date: {course_date}", ln=True, align="C")

    # Certificate ID
    pdf.set_y(-40)
    pdf.set_font(config['font_name'], 'I', 8)
    pdf.set_text_color(128, 128, 128) # Gray color
    pdf.cell(0, 10, f"Certificate ID: {certificate_id}", ln=True, align='C')
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font(config['font_name'], 'I', 10)
    pdf.set_text_color(*config['footer_color'])
    pdf.cell(0, 10, config['footer_text'], ln=True, align='C')

    pdf.output(output_path, "F")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'csv_file' not in request.files:
        flash('No file part in the request. Please choose a CSV file.', 'error')
        return redirect(url_for('index'))
    
    file = request.files['csv_file']
    
    if file.filename == '':
        flash('No file selected. Please choose a CSV file.', 'error')
        return redirect(url_for('index'))
    
    if not file.filename.lower().endswith('.csv'):
        flash('Invalid file type. Please upload a .csv file.', 'error')
        return redirect(url_for('index'))

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            file.save(filepath)
            logger.info(f"File saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            flash(f"Error saving file: {e}", 'error')
            return redirect(url_for('index'))

        generated_filenames_list = []
        failed_certificates_info = []
        
        try:
            instructor_pair = request.form.get('instructor_pair')
            with open(filepath, mode='r', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle BOM
                reader = csv.DictReader(csvfile)
                
                # Check for required headers
                required_headers = ['Person Name', 'Course Name', 'Course Description', 'Course Date']
                if not all(header in reader.fieldnames for header in required_headers):
                    missing_headers = [header for header in required_headers if header not in reader.fieldnames]
                    flash(f"CSV file is missing required columns: {', '.join(missing_headers)}", 'error')
                    return render_template('results.html', message=f"CSV file is missing required columns: {', '.join(missing_headers)}", pdf_files=None)

                parsed_data = list(reader) # Read all data
            
            if not parsed_data:
                flash("CSV file is empty or could not be parsed.", 'warning')
                return render_template('results.html', message="CSV file is empty or could not be parsed.", pdf_files=None)

            logger.info(f"Successfully parsed {len(parsed_data)} rows from CSV.")

            for i, row in enumerate(parsed_data):
                try:
                    person_name = row['Person Name']
                    course_name = row['Course Name']
                    course_description = row['Course Description']
                    course_date = row['Course Date']
                    
                    if not all([person_name, course_name, course_description, course_date]):
                        logger.warning(f"Skipping row {i+1} due to missing data: {row}")
                        failed_certificates_info.append(f"Row {i+1} (Person: {person_name or 'N/A'}) - Missing data")
                        continue

                    certificate_id = generate_certificate_id(person_name, course_name, course_date)
                    output_filename = f"{certificate_id}.pdf"
                    output_path = os.path.join(app.config['GENERATED_PDFS_FOLDER'], output_filename)
                    
                    create_certificate(person_name, course_name, course_description, course_date, certificate_id, output_path, instructor_pair)
                    generated_filenames_list.append(output_filename)
                    logger.info(f"Generated certificate: {output_filename}")

                except KeyError as e:
                    logger.error(f"Missing expected column for row {i+1}: {e}. Data: {row}")
                    failed_certificates_info.append(f"Row {i+1} (Person: {row.get('Person Name', 'N/A')}) - Missing column {e}")
                except Exception as e:
                    logger.error(f"Error generating PDF for row {i+1} (Person: {row.get('Person Name', 'N/A')}): {e}")
                    failed_certificates_info.append(f"Row {i+1} (Person: {row.get('Person Name', 'N/A')}) - {str(e)}")
            
            # Flashing messages based on outcome
            if generated_filenames_list and not failed_certificates_info:
                flash('Successfully generated all certificates!', 'success')
            elif generated_filenames_list and failed_certificates_info:
                flash(f'Successfully generated {len(generated_filenames_list)} PDF(s), but failed for {len(failed_certificates_info)} entries. See details below.', 'warning')
            elif not generated_filenames_list and failed_certificates_info:
                flash(f'Failed to generate any certificates. See details below.', 'error')
            else: # No data or all rows skipped before PDF generation attempt
                 flash('No certificates were generated. Please check your CSV data.', 'warning')


            return render_template('results.html', 
                                   message=f"Processed {len(parsed_data)} rows.", 
                                   pdf_files=generated_filenames_list, 
                                   failed_certificates=failed_certificates_info)

        except FileNotFoundError:
            logger.error(f"Uploaded file not found at path: {filepath}")
            flash("Error: Uploaded file not found. Please try uploading again.", 'error')
            return redirect(url_for('index'))
        except csv.Error as e:
            logger.error(f"CSV parsing error for file {filename}: {e}")
            flash(f"Error parsing CSV file: {e}. Please ensure it's a valid CSV.", 'error')
            return render_template('results.html', message=f"Error parsing CSV file: {e}. Please ensure it's a valid CSV.", pdf_files=None)
        except Exception as e:
            logger.error(f"An unexpected error occurred during processing of {filename}: {e}")
            flash(f"An unexpected error occurred: {e}", 'error')
            return render_template('results.html', message=f"An unexpected error occurred: {e}", pdf_files=None)

@app.route('/generated_pdfs/<path:filename>')
def serve_pdf(filename):
    return send_from_directory(app.config['GENERATED_PDFS_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
