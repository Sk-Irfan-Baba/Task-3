import streamlit as st
import os
import json
import google.generativeai as genai
from serpapi import GoogleSearch


st.set_page_config(page_title="AI Research Agent 🔎", page_icon="🤖", layout="wide")

GEMINI_API_KEY = GEMINI_API_KEY

SERPAPI_API_KEY = SERPAPI_API_KEY

CSS = """
[data-testid="stMetric"] {
    background-color: #333333;
    border: 1px solid #444444;
    padding: 15px;
    border-radius: 10px;
    color: white;
}
[data-testid="stMetric"] .st-ax { color: #a0a0a0; }
.card {
    background-color: #2a2a2a;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    transition: 0.3s;
}
.card:hover { box-shadow: 0 8px 16px rgba(0,0,0,0.2); }
h1, h2, h3, h4, h5, h6 { color: #e0e0e0; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

def get_serpapi_results(query):
    try:
        params = {"engine": "google", "q": query, "api_key": SERPAPI_API_KEY, "gl": "in", "hl": "en"}
        search = GoogleSearch(params)
        results = search.get_dict()
        snippets = []

        if "knowledge_graph" in results:
            snippets.append(results["knowledge_graph"].get("description", ""))

        for section in ["organic_results", "news_results"]:
            if section in results:
                snippets.extend([res.get("snippet", "") for res in results[section]])

        return "\n\n".join(filter(None, snippets)) or "No information found."
    except Exception as e:
        st.error(f"SerpAPI Error: {e}")
        return "No information found."

def parse_gemini_json(text_response):
    try:
        if "```json" in text_response:
            json_str = text_response.split("```json")[1].split("```")[0].strip()
        else:
            json_str = text_response
        return json.loads(json_str)
    except Exception:
        st.error("⚠ Could not parse JSON from AI output.")
        return None

@st.cache_data(show_spinner=False)
def run_research_agent(company, role):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    company_query = f"Overview of {company}: size, domain, and latest news."
    company_context = get_serpapi_results(company_query)
    company_prompt = f"""
    Summarize '{company}' into JSON: {{"size": "...", "domain": "...", "news": ["...", "..."]}}
    Search Results:
    {company_context}
    """
    company_data = parse_gemini_json(model.generate_content(company_prompt).text)

    role_query = f"Job requirements for '{role}' at '{company}': skills, experience, salary."
    role_context = get_serpapi_results(role_query)
    role_prompt = f"""
    Summarize '{role}' at '{company}' into JSON: {{"skills": ["...", "..."], "experience": "...", "salary": "..."}}
    Search Results:
    {role_context}
    """
    role_data = parse_gemini_json(model.generate_content(role_prompt).text)

    return company_data, role_data


st.title("AI Research Agent 🔎")
st.markdown("Get structured company & job role insights in seconds, powered by Gemini & SerpApi.")

with st.sidebar:
    st.header("📝 Research Inputs")
    company_name = st.text_input("Company Name", placeholder="e.g., Google")
    job_role = st.text_input("Job Role", placeholder="e.g., Data Scientist")
    start_btn = st.button("🚀 Start Research", use_container_width=True, type="primary")
    st.markdown("---")

if start_btn:
    if company_name and job_role:
        with st.spinner(f"Researching {company_name}..."):
            company_data, role_data = run_research_agent(company_name, job_role)

        if company_data or role_data:
            st.success("✅ Research Complete!")
            col1, col2 = st.columns(2, gap="large")

            with col1:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader(f"🏢 {company_name} — Overview")
                st.markdown(f"**Company Size:** {company_data.get('size', 'N/A')}")
                st.markdown(f"**🌐 Domain:** {company_data.get('domain', 'N/A')}")
                st.markdown("**📰 Latest News:**")
                for news in company_data.get("news", ["No news found."]):
                    st.markdown(f"- {news}")
                st.markdown('</div>', unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader(f"👨‍💻 Role: {job_role}")
                st.markdown(f"**Experience:** {role_data.get('experience', 'N/A')}")
                st.markdown(f"**Salary Range:** {role_data.get('salary', 'N/A')}")
                st.markdown("**🛠️ Key Skills:**")
                for skill in role_data.get("skills", ["No skills listed."]):
                    st.markdown(f"- {skill}")
                st.markdown('</div>', unsafe_allow_html=True)

            st.divider()
            st.download_button(
                "📥 Download Full Report (JSON)",
                data=json.dumps({"company": company_data, "role": role_data}, indent=2),
                file_name=f"{company_name.replace(' ', '_')}_report.json",
                mime="application/json",
                use_container_width=True
            )
    else:
        st.warning("Please enter both a company name and a job role.")
else:
    st.info("Fill out the details in the sidebar and click **Start Research**.")

