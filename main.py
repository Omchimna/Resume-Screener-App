import streamlit as st
import google.generativeai as genai
import os
import base64
from PIL import Image
import io
import re
import matplotlib.pyplot as plt
import ast # Import ast module for parsing tuple

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

# --- Resume Analysis and Rating Function (Tuple Extraction + Parse Version) ---
def analyze_resume(image_file, job_description, api_key):
    try:
        temp_image_path = "temp_resume.png"
        img = Image.open(image_file)
        img.save(temp_image_path)

        prompt_text = f"""
        Analyze the resume image provided in relation to the following job description:

        Job Description:
        {job_description}

        Based on the resume, provide a rating (out of 5, where 5 is best) for each of the following parameters and a brief justification for each rating (1-2 sentences).  Also, provide an overall percentage fit (0-100%) and a brief overall summary of the resume's suitability.

        **Output Format:**
        Return a Python tuple in the following structure:

        (
            "[Candidate Name (if discernible from resume, else 'Candidate')]",
            [
                [Rating_1 (Years of Experience, integer 1-5), "Justification for Years of Experience (string)"],
                [Rating_2 (Skills Match, integer 1-5), "Justification for Skills Match (string)"],
                [Rating_3 (Projects Relevance, integer 1-5), "Justification for Projects Relevance (string)"],
                [Rating_4 (Working Experience Relevance, integer 1-5), "Justification for Working Experience Relevance (string)"],
                [Rating_5 (Educational History Relevance, integer 1-5), "Justification for Educational History Relevance (string)"]
            ],
            [Overall Fit Percentage (float 0.0-100.0)],
            "[Overall Summary of Resume Suitability (string, 1-2 sentences)]"
        )

        Example Output:
        (
            "Ava Johnson",
            [
                [1, "The resume shows some experience, but not directly related to the fresher role."],
                [2, "Skills partially align, but key skills like Rust are missing."],
                [2, "Projects are not clearly detailed in relation to job requirements."],
                [2, "Work experience is generally relevant but lacks specific technology match."],
                [5, "Excellent educational background in Computer Science."]
            ],
            [20.0],
            "Overall, the resume is a low fit due to lack of specific skills and fresher profile despite a strong education."
        )

                Strictly follow the output format specified above and return it as plain text, without any code formatting or anytype of this text "print(resume_evaluation)"
        """

        gemini_response_text = query_gemini_direct(temp_image_path, prompt_text, api_key)

        if gemini_response_text:
            ratings = {}
            try:
                # --- 1. Extract Tuple Substring ---
                start_index = gemini_response_text.find('(') # Find the first opening parenthesis
                end_index = gemini_response_text.rfind(')') # Find the last closing parenthesis

                if start_index != -1 and end_index != -1 and start_index < end_index:
                    tuple_string = gemini_response_text[start_index : end_index + 1] # Extract substring including parentheses
                else:
                    print("Warning: Could not find valid tuple delimiters in Gemini response.")
                    return None # Or handle error as needed

                # --- 2. Parse Extracted Tuple using ast.literal_eval ---
                parsed_response = ast.literal_eval(tuple_string)


                # --- Structure of parsed_response (tuple) ---
                # parsed_response[0]: Candidate Name (string)
                # parsed_response[1]: List of Ratings and Justifications (list of lists)
                # parsed_response[2]: Overall Fit Percentage (list containing a single float) - IMPORTANT: Gemini might return percentage as list
                # parsed_response[3]: Overall Summary (string)

                candidate_name = parsed_response[0]
                parameter_ratings_data = parsed_response[1]
                overall_fit_percentage_list = parsed_response[2] # It's a list containing a float
                overall_summary = parsed_response[3]

                # --- Extract Ratings and Justifications from parameter_ratings_data ---
                ratings = {}
                ratings["candidate_name"] = candidate_name # Store candidate name
                ratings["overall_summary"] = overall_summary # Store overall summary

                # Parameter Ratings:
                param_names = ["Years of Experience", "Skills Match", "Projects Relevance", "Working Experience Relevance", "Educational History Relevance"]
                for i, param_name in enumerate(param_names):
                    ratings[param_names[i]] = {
                        "rating": parameter_ratings_data[i][0], # Rating is the first element
                        "justification": parameter_ratings_data[i][1] # Justification is the second
                    }

                # Handle Overall Percentage (it's in a list, extract the float):
                if overall_fit_percentage_list and isinstance(overall_fit_percentage_list, list) and len(overall_fit_percentage_list) > 0:
                    ratings["overall_fit_percentage"] = float(overall_fit_percentage_list[0]) # Extract float from list
                else:
                    ratings["overall_fit_percentage"] = None # Handle case if percentage is not properly returned


                return ratings

            except (SyntaxError, ValueError) as e: # Catch parsing errors
                print(f"Error parsing Gemini response (Tuple Extraction + Parse): {e}")
                print("Gemini Response Text that caused parsing error:")
                print(gemini_response_text)
                return None # or return an error indicator as needed


        else:
            return None # Gemini API query failed

    except Exception as e:
        print(f"Error analyzing resume: {e}")
        st.error(f"Detailed Error: {e}")
        return None


# --- Streamlit App ---
st.title("Resume Screener App")

# --- **Hardcoded API Key (Use with caution! For personal use only)** ---
google_api_key = "AIzaSyDkwD7CDw2MmUykHyhvXTbfkjMshMjwudg"  # **Replace with your actual API key**
# --- **End of Hardcoded API Key** ---

job_description = st.text_area("Enter Job Description:", height=200)
uploaded_files = st.file_uploader("Upload Resumes (PNG, JPG, PDF):", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_files and job_description: # Removed google_api_key from here as it's hardcoded
    if not google_api_key.startswith('AIza'):
        st.warning('Please enter your Google API key!', icon='⚠️') # Keep warning in case hardcoded key is invalid, but it will likely always show now
    else:
        st.subheader("Resume Analysis Results:")
        resume_data = []

        num_files = len(uploaded_files)
        completed_files_count = 0

        cols = st.columns([1, 4])

        with cols[0]:
            initial_spinner = st.spinner()

        with cols[1]:
            progress_bar = st.progress(0)
            status_placeholder = st.empty() # Create an empty placeholder for status text


        for index, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            status_placeholder.text(f"Analyzing Resume: {file_name} ({completed_files_count + 1}/{num_files})") # Update placeholder text

            with cols[0]:
                with st.spinner():
                    analysis_result = analyze_resume(uploaded_file, job_description, google_api_key)

            if analysis_result:
                resume_data.append({"filename": file_name, "analysis": analysis_result})
            else:
                resume_data.append({"filename": file_name, "analysis": None, "error": "Analysis failed"})

            completed_files_count += 1
            progress_percent = int((completed_files_count / num_files) * 100)
            with cols[1]:
                 progress_bar.progress(progress_percent)

        with cols[1]:
            status_placeholder.text(f"Analysis Complete. ({completed_files_count}/{num_files} resumes processed)") # Update placeholder for final message


        if resume_data:
            candidate_names = []
            fit_percentages = []

            for data in resume_data:
                if "error" in data:
                    st.error(f"Error during analysis: {data['error']}")
                elif data["analysis"]:
                    analysis = data["analysis"]

                    candidate_name = analysis.get("candidate_name", data['filename']) # Get candidate name from tuple response, fallback to filename
                    st.markdown(f"### Analysis for: {candidate_name}") # Display candidate name (or filename if name not found)


                    candidate_names.append(candidate_name) # Use candidate_name for chart labels
                    fit_percentage = analysis.get("overall_fit_percentage")
                    fit_percentages.append(fit_percentage if fit_percentage is not None else 0) # Handle None percentage for chart


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

                    overall_percentage = analysis.get("overall_fit_percentage") # Already using .get()
                    if overall_percentage is not None:
                        st.metric(label="Overall Fit Percentage", value=f"{overall_percentage:.2f}%")
                    else:
                        st.warning("Could not determine Overall Fit Percentage for this resume.")

                    overall_summary_text = analysis.get("overall_summary") # Get overall summary
                    if overall_summary_text:
                        st.info(f"**Overall Summary:** {overall_summary_text}") # Display overall summary

                else:
                    st.warning(f"No analysis results received for {data['filename']}.")

            if candidate_names and fit_percentages:
                st.subheader("Candidate Fit Comparison")
                # --- Matplotlib Bar Chart ---
                fig, ax = plt.subplots()
                ax.bar(candidate_names, fit_percentages)
                ax.set_xlabel("Candidate")
                ax.set_ylabel("Fit Percentage")
                ax.set_title("Candidate Fit Comparison")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)
                # --- End Matplotlib Bar Chart ---
        else:
            st.info("No resumes were analyzed.")
