# Resume Screener App &nbsp;&nbsp;[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://resume-screener-app.streamlit.app/)  

## Overview

The Resume Screener App is a Streamlit application designed to streamline the initial resume screening process for recruiters and hiring managers.  By providing a job description and uploading resumes (in PDF or image formats), the app analyzes each resume against the job description using Google's Gemini AI model.  It then provides insightful analysis, including parameter-wise ratings, overall fit percentages, radar charts, and comparative bar charts to help quickly assess candidate suitability.

## Key Features

*   **Resume Analysis using Gemini AI:** Leverages Google's Gemini AI model to analyze resume content in relation to a provided job description.
*   **Multi-Format Resume Support:**  Processes resumes in both PDF and image formats (PNG, JPG, JPEG).
*   **Comprehensive Rating System:**  Evaluates resumes based on five key parameters: Years of Experience, Skills Match, Projects Relevance, Working Experience Relevance, and Educational History Relevance.
*   **Detailed Justifications:**  Provides AI-generated justifications for each parameter rating, offering insights into the assessment.
*   **Overall Fit Percentage:** Calculates and displays an overall percentage fit score for each resume against the job description.
*   **Visualizations:** Generates informative radar charts for individual candidate parameter ratings and bar charts for comparing overall fit percentages across multiple candidates.
*   **Multi-Resume Processing with Multithreading:**  Efficiently analyzes multiple resumes concurrently using multithreading, significantly reducing processing time for bulk uploads.
*   **User-Friendly Streamlit Interface:**  Easy-to-use web interface built with Streamlit, allowing for quick input of job descriptions and uploading of resumes.


## Technologies Used

*   **Streamlit:**  For building the interactive web application interface.
*   **Google Gemini API (via `google.generativeai`):** For AI-powered resume analysis and rating.
*   **PyMuPDF (fitz):** For robust PDF parsing and conversion to images.
*   **Pillow (PIL):**  For image processing and handling image-based resumes.
*   **Matplotlib:** For generating charts.
*   **NumPy:** For numerical operations, particularly in chart generation.
*   **Python `threading` and `concurrent.futures`:** For implementing multithreading for faster processing.


## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Omchimna/Resume-Screener-App
    ```

2.  **Install Required Python Libraries:**
    It is recommended to create a virtual environment first:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```
    Then, install the necessary libraries using pip:
    ```bash
    pip install streamlit google-generativeai pillow pymupdf matplotlib numpy
    ```

3.  **Set up Google Gemini API Key:**
    *   Obtain a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).
    *   Open the `model_connection.py` file.
    *   Replace the placeholder `"YOUR_GOOGLE_API_KEY"` in the `google_api_key` variable with your actual API key.
        ```python
        google_api_key = "YOUR_GOOGLE_API_KEY"
        ```

## How to Use

1.  **Run the Streamlit App:**
    Navigate to your project directory in the terminal and run:
    ```bash
    streamlit run main.py
    ```
    This will open the Resume Screener App in your web browser (usually at `http://localhost:8501`).

2.  **Enter Job Description:**
    In the Streamlit app interface, enter or paste the job description for the role you are hiring for into the "Enter Job Description" text area.

3.  **Upload Resumes:**
    Click on the "Browse files" button under "Upload Resumes :" and upload one or more resume files. You can upload PDF files, PNG images, JPG images, or JPEG images.  You can upload multiple resumes at once.

4.  **View Analysis Results:**
    After uploading the resumes, the app will automatically process them and display the analysis results below. For each resume, you will see:
    *   **Parameter Ratings:** Ratings (out of 5) and AI-generated justifications for each of the five key parameters.
    *   **Overall Fit Percentage:**  A percentage score indicating the overall fit of the resume.
    *   **Overall Summary:**  A brief AI-generated summary of the resume's suitability.
    *   **Radar Chart:** A visual representation of the parameter ratings.

5.  **Candidate Comparison Chart:**
    Below the individual resume analyses, a bar chart will be displayed, comparing the overall fit percentages of all uploaded candidates.

## Further Enhancements (Future Considerations)

*   **More Granular Rating Parameters:**  Expanding the rating system to include more specific skills or experience categories.
*   **Keyword Highlighting:**  Visually highlight keywords from the job description within the displayed resume analysis or the resume image itself.
*   **Improved UI/UX:**  Enhancing the Streamlit interface for better user experience and visual appeal.
*   **Advanced Filtering and Sorting:**  Adding features to filter and sort candidate results based on ratings or fit percentages.
*   **Integration with Applicant Tracking Systems (ATS):** Exploring potential integration with ATS platforms for seamless workflow.
*   **Exploring Different Gemini Models/API Features:**  Investigating other Gemini models or API features for potentially improved analysis accuracy or speed.




![](/Screenshot1.png "Screenshot1")