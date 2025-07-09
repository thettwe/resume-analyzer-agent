# Resume Analyzer Agent

Resume Analyzer Agent streamlines the early stages of candidate screening by automating resume analysis and job matching. It leverages AI to evaluate resumes against job descriptions and produces structured, insightful outputs for faster decision-making.

All structured data and analysis results are automatically uploaded to a connected Notion database—where every candidate profile, score, and finding is easily accessible and organized for review.

## Key Features

- **Job Description Ingestion**: Extracts and processes JDs directly from PDF files.
- **Resume Batch Processing**: Supports high-volume CV processing concurrently using `asyncio`, with compatibility for both PDF and DOCX formats.
- **AI-Powered Analysis**: Utilizes Google's Gemini 2.0 Flash model to assess candidate fit based on job requirements.
- **Scoring & Insights**: Generates match scores, ranking categories, and detailed reasoning for each candidate.
- **Notion Integration**: Automatically uploads structured candidate profiles to a connected Notion workspace.
- **Duplicate Handling**: Detects and prevents duplicate entries to keep your Notion database clean and consistent.
- **Real-Time Progress Monitoring**: Displays live updates throughout the batch processing workflow for visibility and control.


## Prerequisites

- Python 3.12 or higher
- Google Gemini API key
- Pre-created Notion database with predefined properties
- Notion API Secrect and Notion database ID
- Internet connection for API access

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/thettwe/resume-analyzer-agent.git
cd resume-analyzer-agent
```

### 2. Set Up Python Environment

#### Using venv (recommended)

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```


### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Unit Tests (Optional)

The project includes comprehensive unit tests for all major functionality. Tests have been fixed and expanded to provide 90% code coverage:

```bash
# Run all tests
python3 -m pytest tests/ -v
```

Key test areas include:

1. File Processing Tests (`test_file_processor.py` & `test_mock_extraction.py`):
   - PDF and DOCX file extraction
   - File discovery and validation

2. API Tests:
   - Gemini API client interaction and response handling
   - Notion database integration and uploads
   - Candidate data extraction and processing

3. Configuration Management:
   - Environment variable handling 
   - CLI parameter overrides
   - Application settings

4. Core Processing Workflow:
   - Input text extraction
   - Async processing with controlled concurrency
   - Structured output formatting  

To generate a coverage report:

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Configuration

### 1. Set Up Environment Variables

Run the setup command to create a template `.env.example` file:

```bash
python3 src/main.py setup
```

### 2. Configure API Keys

Rename `.env.example` to `.env` and edit it with your API keys:

```
# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
TEMPERATURE=0.0

# Notion API Configuration
NOTION_API_KEY=your_notion_api_key_here
NOTION_DATABASE_ID=your_notion_database_id_here

# Optional: Timezone for date/time formatting (default: UTC)
TIMEZONE=UTC
```

### 3. Prepare Notion Database

Ensure your Notion database has the following properties:
- Name (Text)
- Email (Email)
- Phone (Phone)
- Gender (Select)
- Linkedin (URL)
- YOE (Number)
- Profile Summary (Text)
- Professional Skills (Multi-select)
- Personal Skills (Multi-select)
- CV File (Files & media)
- Position Title (Select)
- Location (Select)
- Match Score (Number)
- Ranking Category (Select)
- AI Ranking Reason (Text)
- Processing Date (Date)
- Status (Select)
   - To-do (Processed by AI)
   - In progress (In progress)
   - Complete (Shortlisted, Rejected, Done)

## Usage

The Resume Analyzer Agent is designed to process resumes for multiple job positions efficiently. To do this, you need to organize your files in a specific structure.

### 1. Folder Structure

Create a main "jobs" folder. Inside this folder, create a separate sub-folder for each job position you are hiring for.

For each position folder, you must include:
1.  **A single Job Description (JD) file** in PDF format (`.pdf`).
2.  **A sub-folder named `CVs`** containing all the candidate resumes for that position. Supported resume formats are `.pdf` and `.docx`.

Here is an example of the required structure:

```
/path/to/your/jobs_folder/
├── Software-Engineer/
│   ├── Software-Engineer-JD.pdf
│   └── CVs/
│       ├── candidate1.pdf
│       ├── candidate2.docx
│       └── ...
└── Data-Analyst/
    ├── Data-Analyst-JD.pdf
    └── CVs/
        ├── candidate3.pdf
        └── ...
```

### 2. Run the Process Command

Once your folders are set up, run the `process` command and point it to your main jobs folder:

```bash
python3 src/main.py process "/path/to/your/jobs_folder"
```

The agent will automatically traverse each position folder, find the JD, and process all resumes within the corresponding `CVs` sub-folder.

### 3. Command Options

You can override the settings from your `.env` file by using the following command-line options:

```bash
python3 src/main.py process "/path/to/your/jobs_folder" --notion-db "your-notion-db-id" --gemini-model "gemini-1.5-flash"
```

Available options:
- `--notion-db` / `-nd`: Override Notion Database ID
- `--notion-api-key` / `-na`: Override Notion API Key
- `--gemini-api-key` / `-ga`: Override Gemini API Key
- `--gemini-model` / `-gm`: Override Gemini Model
- `--gemini-temperature` / `-gt`: Override Gemini Temperature
- `--timezone` / `-tz`: Override Timezone for date/time formatting (default: UTC)
- `--gemini-concurrency` / `-gc`: Maximum number of concurrent Gemini API calls (default: 5)
- `--notion-concurrency` / `-nc`: Maximum number of concurrent Notion uploads (default: 3)

## Project Structure

```
src/
├── app.py                    # Main entry point
├── main.py                   # Application initialization
├── api/                      # API client implementations
│   ├── gemini.py             # Gemini API client
│   ├── notion.py             # Notion API client
│   ├── models.py             # Data models
│   └── prompts.py            # Gemini prompt templates
├── commands/                 # CLI command implementations
│   ├── process.py            # Process command logic
│   └── setup.py              # Setup command logic
├── config/                   # Configuration management
│   ├── config.py             # Environment variables management
│   └── settings.py           # Application settings
├── core/                     # Core processing functionality
│   ├── extraction.py         # CV text extraction
│   ├── gemini_processing.py  # Gemini API integration
│   ├── notion_upload.py      # Notion upload functionality
│   └── processing.py         # Main processing workflow
├── misc/                     # Miscellaneous utilities
│   ├── file_processor.py     # PDF/DOCX file processing
│   └── utils.py              # Helper functions
```

## Supported File Formats

The Resume Analyzer Agent supports:
- PDF files (.pdf)
- Microsoft Word documents (.docx)

## Troubleshooting

### API Connection Issues

- Check internet connection
- Validate API keys in your `.env` file
- Ensure Notion database ID is correct

### File Processing Issues

- Make sure files are not corrupted or password-protected
- Confirm read permissions & path for input files

### Empty Processing Results

- Ensure the job description contains valid text
- Confirm CV folder contains supported file formats
- Check model and region compatibility for Gemini

## Performance Considerations

- Processing time depends on CV count, filesize and content complexity
- Async processing speeds up throughput
- Gemini API rate limits may impact overall performance

## License

This project is licensed under the MIT License.

## Acknowledgments

- Google Generative AI for the Gemini API
- Notion API for database integration
- The Python open-source community
