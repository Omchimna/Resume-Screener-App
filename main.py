import streamlit as st
import google.generativeai as genai
import os
import base64
from PIL import Image
import io
import re

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
    try:
        temp_image_path = "temp_resume.png"
        img = Image.open(image_file)
        img.save(temp_image_path)

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
        """

        gemini_response_text = query_gemini_direct(temp_image_path, prompt_text, api_key)

        if gemini_response_text:
            ratings = {}
            lines = gemini_response_text.strip().split('\n')
            for line in lines:
                if "Rating:" in line:
                    parts = line.split("Rating:")
                    parameter_name = parts[0].strip().rstrip(':')
                    rating_and_justification = parts[1].strip().split(', Justification:')
                    rating_str = rating_and_justification[0].split('/')[0].strip()
                    justification = rating_and_justification[1].strip() if len(rating_and_justification) > 1 else "N/A"

                    try:
                        rating_value = int(rating_str)
                        ratings[parameter_name] = {"rating": rating_value, "justification": justification}
                    except ValueError:
                        print(f"Warning: Could not parse rating value from line: {line}")

                elif "Overall Fit Percentage:" in line:
                    # --- Improved Percentage Parsing using Regex ---
                    import re  # Import regular expression module

                    percentage_match = re.search(r'(\d+\.?\d*)%', line) # Regex to find numbers ending with %
                    if percentage_match:
                        percentage_str = percentage_match.group(1) # Extract the captured number (group 1)
                        try:
                            ratings["overall_fit_percentage"] = float(percentage_str)
                        except ValueError:
                            ratings["overall_fit_percentage"] = None
                            print(f"Warning: Could not parse percentage value (regex failed to convert to float) from line: {line}")
                    else:
                        ratings["overall_fit_percentage"] = None
                        print(f"Warning: Could not parse percentage value (regex no match) from line: {line}")
                    # --- End Improved Percentage Parsing ---
            return ratings
        else:
            return None

    except Exception as e:
        print(f"Error analyzing resume: {e}")
        st.error(f"Detailed Error: {e}")
        return None


# --- Streamlit App ---
st.title("Resume Screener App")

# --- **Hardcoded API Key (Use with caution! For personal use only)** ---
#google_api_key = "AIzaSyDkwD7CDw2MmUykHyhvXTbfkjMshMjwudg"  # **Replace with your actual API key**
google_api_key = os.environ['GOOGLE_API_KEY']  # **Replace with your actual API key**
# --- **End of Hardcoded API Key** ---


job_description = st.text_area("Enter Job Description:", height=200)
uploaded_files = st.file_uploader("Upload Resumes (PNG, JPG, PDF):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_files and job_description: # Removed google_api_key from here as it's hardcoded
    if not google_api_key.startswith('AIza'):
        st.warning('Please enter your Google API key!', icon='⚠️') # Keep warning in case hardcoded key is invalid, but it will likely always show now
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
                    resume_data.append({"filename": file_name, "analysis": None, "error": "Analysis failed"})


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
                    fit_percentages.append(analysis.get("overall_fit_percentage", 0))

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
