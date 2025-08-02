# Certificate PDF Generator

A Flask web application that takes a CSV file as input and generates individual PDF certificates for each row of data.

## Features

- Upload CSV file.
- Generate PDF certificates based on CSV data.
- Download individual PDF certificates.
- Basic error handling for file types and CSV format.

## Prerequisites

- Python 3.x
- Pip

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/certificate-pdf-generator.git
    ```
    *(Replace `https://github.com/yourusername/certificate-pdf-generator.git` with the actual repository URL when available.)*

2.  **Navigate to the project directory:**
    ```bash
    cd certificate-pdf-generator
    ```
    *(Adjust `certificate-pdf-generator` if your root directory is named differently.)*

3.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

4.  **Activate the virtual environment:**
    -   On Linux/macOS:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        venv\Scripts\activate
        ```

5.  **Install dependencies:**
    ```bash
    pip install -r certificate_generator/requirements.txt
    ```

## Running the Application

1.  **Set the Flask application environment variable:**
    -   On Linux/macOS:
        ```bash
        export FLASK_APP=certificate_generator.app
        ```
    -   On Windows:
        ```bash
        set FLASK_APP=certificate_generator.app
        ```

2.  **(Optional) Enable development mode for live reloading and debugger:**
    *(The application's `app.py` uses `app.run(debug=True)`, which enables these features when run directly with `python certificate_generator/app.py`. The `FLASK_ENV` variable is standard for use with the `flask run` command.)*
    -   On Linux/macOS:
        ```bash
        export FLASK_ENV=development
        ```
    -   On Windows:
        ```bash
        set FLASK_ENV=development
        ```

3.  **Run the Flask development server:**
    There are two main ways to run the application:
    -   Using the `flask` command (requires `FLASK_APP` to be set):
        ```bash
        flask run
        ```
    -   Directly running the `app.py` script:
        ```bash
        python certificate_generator/app.py
        ```

4.  **Open your web browser and go to:**
    `http://127.0.0.1:5000/`

## CSV File Format

The application expects a CSV file with the following headers in the first row:

-   `Person Name`: The name of the person receiving the certificate.
-   `Course Name`: The name of the course.
-   `Course Description`: A brief description of the course.
-   `Course Date`: The date the course was completed (e.g., YYYY-MM-DD or any consistent date format).

**Example CSV:**
```csv
Person Name,Course Name,Course Description,Course Date
Alice Smith,Python Programming,Learn Python basics,2023-01-15:2023-01-16
Bob Johnson,Advanced Web Development,Master front-end and back-end,2023-02-20:2023-02-22
```

## Usage

1.  Navigate to the home page (e.g., `http://127.0.0.1:5000/`).
2.  Click "Choose CSV file:" (or similar, depending on your browser's rendering of the file input) and select your prepared CSV file.
3.  Click "Upload and Generate Certificates".
4.  The results page will display a status message. 
    - If successful, links to download the generated PDF certificates will be provided.
    - If there were any errors during processing (e.g., issues with specific rows in the CSV, incorrect file type, missing headers), these will be indicated on the page, often with details about which rows failed.

## Running Tests

1.  Ensure you are in the root project directory (e.g., `certificate-pdf-generator`).
2.  Activate your virtual environment if you haven't already.
3.  All necessary dependencies for running tests are included in `certificate_generator/requirements.txt`.
4.  Run the tests using the `unittest` module:
    ```bash
    python -m unittest discover -s tests
    ```
    Alternatively, to run a specific test file:
    ```bash
    python -m unittest tests/test_app.py
    ```

---

*This README provides a guide to setting up, running, and using the Certificate PDF Generator application.*
