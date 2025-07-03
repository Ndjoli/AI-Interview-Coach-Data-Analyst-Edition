import streamlit as st
import json
import openai
import os
from fpdf import FPDF

# ✅ Securely load your OpenAI API key from environment variable
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Persona prompt templates
persona_prompts = {
    "Professional Coach": "You are a professional interview coach. Give clear, encouraging, STAR-based feedback to improve the candidate's answer.",
    "Mentor": "You are a mentor providing supportive feedback. Offer suggestions while staying positive and constructive.",
    "Technical Reviewer": "You are a senior data analyst reviewing answers critically for technical accuracy, detail, and completeness.",
    "Tough Critic": "You are a strict interviewer. Give blunt, honest feedback and point out flaws clearly but constructively."
}

# ✅ Load question bank
with open("prompts/question_bank.json", "r") as f:
    question_data = json.load(f)
question_list = question_data["data_analyst"]

# ✅ Streamlit UI
st.set_page_config(page_title="AI Interview Coach")
st.title("🎤 AI Interview Coach – Data Analyst Edition")
st.markdown("Practice behavioral interview questions and receive AI feedback using the STAR method.")

# ✅ Persona selector
persona = st.selectbox("Choose your AI Coach Persona:", list(persona_prompts.keys()))
system_prompt = persona_prompts[persona]

# ✅ Session state
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "responses" not in st.session_state:
    st.session_state.responses = []
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

index = st.session_state.question_index
question = question_list[index]

st.subheader(f"Question {index + 1} of {len(question_list)}")
st.write(question)

# ✅ Text area (auto-clear)
st.session_state.user_input = st.text_area("Your Answer", value=st.session_state.user_input, height=200)

if st.button("Submit Answer"):
    if st.session_state.user_input.strip() == "":
        st.warning("Please write your answer before submitting.")
    else:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}"},
            {"role": "user", "content": f"Answer: {st.session_state.user_input}"}
        ]
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            st.success(reply)
            st.session_state.responses.append((question, st.session_state.user_input, reply))
        except Exception as e:
            st.error(f"Error: {e}")

if st.button("Next Question"):
    if index + 1 < len(question_list):
        st.session_state.question_index += 1
        st.session_state.user_input = ""  # Clear input box
    else:
        st.success("🎉 You’ve completed all questions!")

# ✅ Sidebar Summary
if st.session_state.responses:
    st.sidebar.title("📋 Review Summary")
    for i, (q, a, r) in enumerate(st.session_state.responses):
        st.sidebar.markdown(f"**Q{i+1}:** {q}")
        st.sidebar.markdown(f"- **Answer:** {a}")
        st.sidebar.markdown(f"- **AI Feedback:** {r}")
        st.sidebar.markdown("---")

# ✅ Show PDF button only after final question
if st.session_state.question_index + 1 == len(question_list):
    if st.button("📥 Download PDF Summary"):

        def clean_text(text):
            return text.replace("–", "-").encode("latin-1", "replace").decode("latin-1")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, "AI Interview Coach - Summary", ln=True)
        pdf.ln(5)

        for i, (q, a, r) in enumerate(st.session_state.responses, start=1):
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(0, 10, clean_text(f"Question {i}: {q}"))
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 10, clean_text(f"Your Answer:\n{a}"))
            pdf.multi_cell(0, 10, clean_text(f"AI Feedback:\n{r}"))
            pdf.ln(5)

        pdf_file = "interview_summary.pdf"
        pdf.output(pdf_file)

        with open(pdf_file, "rb") as f:
            st.download_button("⬇️ Download PDF", f, file_name=pdf_file)