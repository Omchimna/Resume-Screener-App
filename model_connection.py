import streamlit as st
import google.generativeai as genai
from PIL import Image
import ast
import pymupdf


google_api_key = st.secrets["GOOGLE_API_KEY"] 


# --- Gemini API Interaction Function ---
def query_gemini_direct(image_path: str, text_query: str) -> str: # Removed api_key parameter
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
def analyze_resume(uploaded_file, job_description): # Changed file to uploaded_file, removed api_key parameter
    try:
        # file_name = uploaded_file.name
        # file_type = uploaded_file.type
        temp_image_path = "temp_resume.png"
        image_data = None # No longer needed
        mime_type = None # No longer needed

        if uploaded_file.type == "application/pdf":
            img = pdf_To_Img(uploaded_file)
        elif uploaded_file.type.startswith("image/"): # Handle image files (png, jpg, jpeg)
            img = Image.open(uploaded_file) # Open directly as PIL Image
        else:
            raise ValueError(f"Unsupported file type: {uploaded_file.type} for file: {uploaded_file.name}")

        # --- Now, process the PIL Image ---
        img.save(temp_image_path) # Save as temp PNG for Gemini

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

        gemini_response_text = query_gemini_direct(temp_image_path, prompt_text) # Removed api_key parameter

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
        else: # Should not reach here due to file type check at the beginning, but for robustness
            return None

    except Exception as e:
        print(f"Error analyzing resume: {e}")
        st.error(f"Detailed Error: {e}")
        return None


def pdf_To_Img(pdf_file):
    doc = pymupdf.open(pdf_file)
    if len(doc)>1:      
        new_im=Image.new('RGB', (4000,10000))
        i,pix=0,0
        while(i<len(doc)):
            im=doc[i].get_pixmap(matrix=pymupdf.Identity,dpi=250).pil_image()
            new_im.paste(im, (0,pix))
            i+=1
            pix+=(((im.size)[1])+2)
            
        return new_im

    elif len(doc)==1:
        return doc[0].get_pixmap(matrix=pymupdf.Identity,dpi=250).pil_image()
