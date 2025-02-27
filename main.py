import streamlit as st
import google.generativeai as genai
import os
import base64
from PIL import Image
import io

# --- Gemini API Interaction Function ---
def query_gemini_direct(image_path: str, text_query: str, google_api_key: str) -> str:
    try:
        genai.configure(api_key=google_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        image_part = {
            'mime_type': 'image/png', # Adjust as needed based on file type
            'data': image_data
        }
        text_part = text_query
        contents = [image_part, text_part]
        response = model.generate_content(contents=contents)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error querying Gemini API (Direct - 1.5-flash): {e}")
        return None

# --- Resume Analysis and Rating Function ---
def analyze_resume(image_file, job_description, api_key):
    """
    Analyzes a single resume image against a job description using Gemini API and provides ratings.

    Args:
        image_file: Uploaded file object (resume image).
        job_description: Text of the job description.
        api_key: Google API key.

    Returns:
        dict: Dictionary containing ratings for different parameters and overall fit percentage.
              Returns None if there's an error in analysis.
    """
    try:
        # Save uploaded file temporarily to disk for processing
        temp_image_path = "temp_resume.png" # You can use a more robust temp file mechanism if needed
        img = Image.open(image_file)
        img.save(temp_image_path)


        # Construct Gemini prompt - Adjusted for structured output
        prompt_text = f"""
        Analyze the resume image provided in relation to the following job description:

        Job Description:
        {job_description}

        Based on the resume, provide a rating (out of 5, where 5 is best) for each of the following parameters based on how well the resume aligns with the job description.
        Also, provide a brief justification for each rating (1-2 sentences):

        Parameters to Rate:
        1. Years of Experience:  Rating: [Rating]/5, Justification: [Justification]
        2. Skills Match: Rating: [Rating]/5, Justification: [Justification]
        3. Projects Relevance: Rating: [Rating]/5, Justification: [Justification]
        4. Working Experience Relevance: Rating: [Rating]/5, Justification: [Justification]
        5. Educational History Relevance: Rating: [Rating]/5, Justification: [Justification]

        Finally, calculate an overall percentage fit (0-100%) of this resume for the job description.
        Overall Fit Percentage: [Percentage]%

        --- Response format example --- (Do not include this in your actual response, just follow the format)
        1. Years of Experience: Rating: 4/5, Justification: Good experience in related field.
        2. Skills Match: Rating: 5/5, Justification:  Excellent alignment with required skills.
        ...
        Overall Fit Percentage: 85%
        """

        gemini_response_text = query_gemini_direct(temp_image_path, prompt_text, api_key)


        if gemini_response_text:
            ratings = {}
            lines = gemini_response_text.strip().split('\n')
            for line in lines:
                if "Rating:" in line:
                    parts = line.split("Rating:")
                    parameter_name = parts[0].strip().rstrip(':') # Extract parameter name
                    rating_and_justification = parts[1].strip().split(', Justification:')
                    rating_str = rating_and_justification[0].split('/')[0].strip() # Get just the rating number
                    justification = rating_and_justification[1].strip() if len(rating_and_justification) > 1 else "N/A"

                    try:
                        rating_value = int(rating_str)
                        ratings[parameter_name] = {"rating": rating_value, "justification": justification}
                    except ValueError:
                        print(f"Warning: Could not parse rating value from line: {line}")


                elif "Overall Fit Percentage:" in line:
                    percentage_str = line.split("Overall Fit Percentage:")[1].strip().rstrip('%')
                    try:
                        ratings["overall_fit_percentage"] = float(percentage_str)
                    except ValueError:
                        ratings["overall_fit_percentage"] = None
                        print(f"Warning: Could not parse percentage value from line: {line}")

            os.remove(temp_image_path) # Clean up temp image file
            return ratings
        else:
            os.remove(temp_image_path)
            return None

    except Exception as e:
        print(f"Error analyzing resume: {e}")
        return None


# --- Streamlit App ---
st.title("Resume Screener App")

google_api_key = st.text_input("Enter your Google API Key:", type="password")
job_description = st.text_area("Enter Job Description:", height=200)
uploaded_files = st.file_uploader("Upload Resumes (PNG, JPG, PDF):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_files and job_description and google_api_key:
    if not google_api_key.startswith('AIza'):
        st.warning('Please enter your Google API key!', icon='⚠️')
    else:
        st.subheader("Resume Analysis Results:")
        resume_data = []

        with st.spinner("Analyzing Resumes... Please wait..."):
            for uploaded_file in uploaded_files:
                file_name = uploaded_file.name
                analysis_result = analyze_resume(uploaded_file, job_description, google_api_key)

                if analysis_result:
                    resume_data.append({"filename": file_name, "analysis": analysis_result})
                else:
                    resume_data.append({"filename": file_name, "analysis": None, "error": "Analysis failed"}) # Indicate analysis failure


        if resume_data:
            candidate_names = []
            fit_percentages = []

            for data in resume_data:
                st.markdown(f"### Analysis for: {data['filename']}")
                if "error" in data:
                    st.error(f"Error during analysis: {data['error']}")
                elif data["analysis"]:
                    analysis = data["analysis"]

                    candidate_names.append(data["filename"])
                    fit_percentages.append(analysis.get("overall_fit_percentage", 0)) # Default to 0 if percentage missing

                    # Display Parameter Ratings and Justifications
                    if analysis.get("Years of Experience"):
                        st.write(f"- **Years of Experience:** Rating: {analysis['Years of Experience']['rating']}/5")
                        st.caption(f"  *Justification:* {analysis['Years of Experience']['justification']}")
                    if analysis.get("Skills Match"):
                        st.write(f"- **Skills Match:** Rating: {analysis['Skills Match']['rating']}/5")
                        st.caption(f"  *Justification:* {analysis['Skills Match']['justification']}")
                    if analysis.get("Projects Relevance"):
                        st.write(f"- **Projects Relevance:** Rating: {analysis['Projects Relevance']['rating']}/5")
                        st.caption(f"  *Justification:* {analysis['Projects Relevance']['justification']}")
                    if analysis.get("Working Experience Relevance"):
                        st.write(f"- **Working Experience Relevance:** Rating: {analysis['Working Experience Relevance']['rating']}/5")
                        st.caption(f"  *Justification:* {analysis['Working Experience Relevance']['justification']}")
                    if analysis.get("Educational History Relevance"):
                        st.write(f"- **Educational History Relevance:** Rating: {analysis['Educational History Relevance']['rating']}/5")
                        st.caption(f"  *Justification:* {analysis['Educational History Relevance']['justification']}")

                    overall_percentage = analysis.get("overall_fit_percentage")
                    if overall_percentage is not None:
                        st.metric(label="Overall Fit Percentage", value=f"{overall_percentage:.2f}%")
                    else:
                        st.warning("Could not determine Overall Fit Percentage for this resume.")

                else:
                    st.warning(f"No analysis results received for {data['filename']}.")

            if candidate_names and fit_percentages:
                st.subheader("Candidate Fit Comparison")
                chart_data = {"Candidate": candidate_names, "Fit Percentage": fit_percentages}
                st.bar_chart(chart_data, x="Candidate", y="Fit Percentage")
        else:
            st.info("No resumes were analyzed.")