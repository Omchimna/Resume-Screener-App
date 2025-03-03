import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from model_connection import analyze_resume
import threading
import concurrent.futures  # Import for ThreadPoolExecutor


# --- Function to Generate Radar Chart ---
def generate_radar_chart(candidate_name, ratings):
    """Generates a radar chart for candidate ratings."""
    categories = ["Years of Exp.", "Skills Match", "Projects Rel.", "Work Exp. Rel.", "Education Rel."]  # Shortened for labels
    data_values = [
        ratings["Years of Experience"]["rating"],
        ratings["Skills Match"]["rating"],
        ratings["Projects Relevance"]["rating"],
        ratings["Working Experience Relevance"]["rating"],
        ratings["Educational History Relevance"]["rating"]
    ]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False)
    data_values = np.concatenate((data_values, [data_values[0]]))  # Close the polygon
    angles = np.concatenate((angles, [angles[0]]))  # Close the polygon

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))  # Adjust size

    fig.set_facecolor('#0E1117')
    ax.plot(angles, data_values, 'o-', linewidth=2)  # Added markers
    ax.fill(angles, data_values, alpha=0.25)
    ax.set_facecolor('#0E1117')

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, color="white")
    ax.set_yticks(range(6))  # Ensure ticks are at 0, 1, 2, 3, 4, 5
    ax.set_yticklabels(['0', '1', '2', '3', '4', '5'], color="white")  # Set y-axis ticks for ratings 0-5 (adjust as needed)
    # ax.set_yticklabels(5)
    ax.set_ylim(0, 5)  # Set y-axis limits to 0-5

    ax.set_title(f"Parameter Ratings for {candidate_name}", y=1.05, color="white")  # Title outside plot area
    ax.title.set_fontsize(14)  # Adjust title fontsize

    return fig


# --- Streamlit App ---
st.title("Resume Screener App")

job_description = st.text_area("Enter Job Description:", height=200)
uploaded_files = st.file_uploader("Upload Resumes :", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

if uploaded_files and job_description:
    st.subheader("Resume Analysis Results:")
    resume_data = []
    candidate_names = []  # Lists to store data for bar chart
    fit_percentages = []  # Lists to store data for bar chart

    num_files = len(uploaded_files)
    completed_files_count = 0

    cols = st.columns([1, 4])  # Define columns for progress elements

    with cols[0]:  # Spinner in the first column
        initial_spinner = st.spinner()

    with cols[1]:  # Progress bar and status in the second column
        progress_bar = st.progress(0)
        status_placeholder = st.empty()  # Create an empty placeholder for status text

    # --- Multithreading Implementation using ThreadPoolExecutor ---
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers as needed
        futures = []  # List to store future objects

        for index, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            status_placeholder.text(f"Analyzing Resume: {file_name} ({completed_files_count + 1}/{num_files})")  # Update placeholder text

            # Submit the analysis task to the thread pool
            future = executor.submit(analyze_resume, uploaded_file, job_description)  # Submit task
            futures.append(future)  # Add future to the list

        # --- Process results as threads complete ---
        for future in concurrent.futures.as_completed(futures):  # Iterate as futures complete
            analysis_result = future.result()  # Get result from thread

            uploaded_file_for_result = uploaded_files[futures.index(future)] # Get corresponding uploaded_file for results display
            file_name = uploaded_file_for_result.name

            with cols[0]:  # Spinner context for each file
                with st.spinner():
                    if analysis_result:
                        resume_data.append({"filename": file_name, "analysis": analysis_result})

                        # Collect data for bar chart here, AFTER successful analysis
                        candidate_name = analysis_result.get("candidate_name", file_name)  # Corrected to analysis_result
                        candidate_names.append(candidate_name)
                        fit_percentage = analysis_result.get("overall_fit_percentage")  # Corrected to analysis_result
                        fit_percentages.append(fit_percentage if fit_percentage is not None else 0)

                    else:
                        resume_data.append({"filename": file_name, "analysis": None, "error": "Analysis failed"})

            completed_files_count += 1
            progress_percent = int((completed_files_count / num_files) * 100)
            with cols[1]:  # Progress bar update in the second column
                progress_bar.progress(progress_percent)


    with cols[1]:  # Completion message in the second column, after ALL threads are done
        status_placeholder.text(f"Analysis Complete. ({completed_files_count}/{num_files} resumes processed)")  # Update placeholder for final message


    if resume_data:
        for data in resume_data:
            if "error" in data:
                st.error(f"Error during analysis: {data['error']}")
            elif data["analysis"]:
                analysis = data["analysis"]
                candidate_name = analysis.get("candidate_name", data['filename'])  # Get candidate name

                col1, col2 = st.columns([7, 3])  # Columns for each resume analysis

                with col1:  # Ratings and Justifications in the first column
                    st.markdown(f"### Analysis for: {candidate_name}")  # Candidate name header

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

                    overall_percentage = analysis.get("overall_fit_percentage")  # Already using .get()
                    if overall_percentage is not None:
                        st.metric(label="Overall Fit Percentage", value=f"{overall_percentage:.2f}%")
                    else:
                        st.warning("Could not determine Overall Fit Percentage for this resume.")

                    overall_summary_text = analysis.get("overall_summary")  # Get overall summary
                    if overall_summary_text:
                        st.info(f"**Overall Summary:** {overall_summary_text}")  # Display overall summary

                with col2:  # Radar chart in the second column
                    radar_fig = generate_radar_chart(candidate_name, analysis)
                    st.pyplot(radar_fig)
                    plt.close(radar_fig)  # Close figure to prevent display issues
            st.write("---")

        # --- Bar Chart for Candidate Comparison ---
        if candidate_names and fit_percentages:
                st.subheader("Candidate Fit Comparison")
                fig_bar, ax_bar = plt.subplots()
                fig_bar.set_facecolor('#60709f')
                ax_bar.bar(candidate_names, fit_percentages)
                ax_bar.set_xlabel("Candidate")
                ax_bar.set_xticklabels(candidate_names)
                ax_bar.set_ylabel("Fit Percentage")
                ax_bar.set_title("Overall Candidate Fit Comparison",color="white") # More descriptive title
                ax_bar.set_facecolor('#60709f')
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig_bar)
                plt.close(fig_bar) # Close bar chart figure
                                        
    else:
        st.info("No resumes were analyzed.")
