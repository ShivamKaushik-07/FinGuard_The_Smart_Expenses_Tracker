# FinGuard - Smart Expense Tracker

FinGuard is an expense tracking application that helps users manage their finances through various input methods including voice commands and bill scanning.

## Features

### 1. Dashboard
- View expense summaries by day, month, and year
- Track budget status with visual indicators
- Get notifications when approaching budget limits

### 2. Bill Scanner
- Upload images of receipts and bills
- Automatic OCR to extract expense details
- Intelligent amount and date detection

### 3. Voice Input
- Add expenses by speaking into your microphone
- Simple voice commands for quick expense entry

### 4. Data Export
- Export expense data to CSV and PDF formats
- Generate monthly reports

## Installation

### Prerequisites

1. **Python 3.8+** - Make sure you have Python 3.8 or newer installed
2. **Tesseract OCR** - Required for bill scanning functionality
   - Windows: Download and install from [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`
3. **PortAudio** - Required for PyAudio (microphone support)
   - Windows: Automatically installed with PyAudio
   - macOS: `brew install portaudio`
   - Linux: `sudo apt-get install portaudio19-dev`
4. **wkhtmltopdf** - Required for PDF expense reports (optional)
   - Windows: Download and install from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
   - macOS: `brew install wkhtmltopdf`
   - Linux: `sudo apt-get install wkhtmltopdf`

### Setup Steps

1. **Clone the repository**
   ```
   git clone <repository-url>
   cd FinGuard
   ```

2. **Create a virtual environment (recommended)**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. **Install Python dependencies**
   ```
   pip install -r requirements.txt
   ```
   
   This will install the following packages:
   - Flask 3.0.3 - Web framework
   - Flask-Cors 4.0.0 - For cross-origin requests
   - Flask-Login - For user authentication
   - Flask-Migrate - For database migrations
   - SpeechRecognition 3.10.1 - For voice input
   - PyAudio 0.2.14 - For microphone support
   - OpenCV (opencv-python 4.9.0.80) - For image processing
   - Pytesseract 0.3.10 - OCR tool for text extraction
   - Pillow 10.3.0 - Image handling
   - NumPy 1.26.4 - Numeric operations
   - Pandas 2.2.2 - Data manipulation
   - Scikit-learn 1.4.2 - Machine learning
   - Joblib 1.4.2 - Model persistence
   - Matplotlib 3.9.0 - For charts and visualizations
   - Plotly 5.22.0 - Interactive charts
   - python-dotenv 1.0.1 - Environment variable management
   - Twilio - For SMS OTP functionality

5. **Configure Tesseract path**
   - Make sure the Tesseract executable is in your system PATH or
   - Update the path in `app/routes.py` if needed:
     ```python
     pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
     ```

6. **Configure OTP Services (Optional)**
   - For Email OTP functionality:
     - Update the sender email and app password in `app/utils.py`
     - For Gmail, you'll need to create an App Password in your Google Account
   - For SMS OTP functionality:
     - Create a Twilio account at https://www.twilio.com
     - Get your Account SID and Auth Token
     - Update these credentials in `app/utils.py`

7. **Initialize the database**
   ```
   python init_db.py
   ```

8. **Run the application**
   ```
   python run.py
   ```

9. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:5000`

## Troubleshooting

### PyAudio Installation Issues

- **Windows**: If you encounter errors installing PyAudio, try using a precompiled wheel:
  ```
  pip install pipwin
  pipwin install pyaudio
  ```

- **macOS**: If you encounter issues with PyAudio installation:
  ```
  brew install portaudio
  pip install --global-option='build_ext' --global-option='-I/usr/local/include' --global-option='-L/usr/local/lib' pyaudio
  ```

- **Linux**: If PyAudio installation fails:
  ```
  sudo apt-get install python3-pyaudio
  ```

### Tesseract OCR Issues

- **Path not found**: Ensure Tesseract is properly installed and the path is correctly set in the code
- **OCR quality**: For better OCR results, ensure images are clear and well-lit
- **Language support**: Install additional language packs if needed:
  - Windows: Use the installer and select additional languages
  - Linux: `sudo apt-get install tesseract-ocr-[lang]` (replace [lang] with language code)

### Database Issues

- If you encounter database errors, try resetting the database:
  ```
  python reset_db.py
  ```

- Alternatively, you can manually delete the database file and reinitialize:
  ```
  # On Windows
  del instance\FinGuard.db
  # On macOS/Linux
  rm instance/FinGuard.db
  
  # Then reinitialize
  python init_db.py
  ```

- The application includes automatic monthly expense reset functionality:
  - On the first day of each month, the system automatically:
    - Exports the previous month's expenses to CSV and PDF formats
    - Saves these exports in the `app/exports` directory
    - Resets the expense data for all users
  - This functionality is implemented in `app/backup.py` and triggered in `run.py`

### Voice Recognition Issues

- Ensure your microphone is properly connected and has necessary permissions
- Speak clearly and in a quiet environment
- Check your internet connection (Google Speech Recognition requires internet)

### Text-to-Speech Issues

- If you don't hear voice responses:
  - Check your system's audio output settings
  - Ensure your speakers or headphones are connected and working
  - On Windows, you may need to install additional voices through Windows Settings > Time & Language > Speech
  - On macOS, check System Preferences > Accessibility > Speech
  - On Linux, you may need to install additional speech engines like `espeak`

## System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Processor**: 1.6 GHz or faster
- **Memory**: 4 GB RAM minimum (8 GB recommended)
- **Storage**: 500 MB available space
- **Internet Connection**: Required for voice recognition
- **Microphone**: Required for voice input features
- **Python**: 3.8 or newer

## Project Structure

```
FinGuard/
├── app/                      # Main application package
│   ├── __init__.py          # Flask application factory
│   ├── auth.py              # Authentication routes and logic
│   ├── backup.py            # Monthly expense reset and export functionality
│   ├── db_manager.py        # Database models and configuration
│   ├── exports/             # Directory for exported expense reports
│   ├── routes.py            # Main application routes
│   ├── static/              # Static assets (CSS, JS, images)
│   ├── templates/           # HTML templates
│   ├── utils.py             # Utility functions (OTP, etc.)
│   └── voice_input.py       # Voice input processing
├── data/                    # Data storage directory
├── init_db.py               # Database initialization script
├── instance/                # Instance-specific data (database file)
├── model/                   # ML models (if applicable)
├── requirements.txt         # Python dependencies
├── reset_db.py              # Database reset script
├── run.py                   # Application entry point
└── test_otp_sending.py      # OTP functionality test script
```