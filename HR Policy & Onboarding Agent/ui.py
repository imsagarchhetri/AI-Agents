import streamlit as st
import requests
import os
import json

st.set_page_config(page_title="HR Policy & Onboarding Agent", page_icon="🏢", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("🏢 HR Policy & Onboarding Agent")
st.markdown("An AI-powered HR Assistant for autonomous employee onboarding and policy Q&A.")

tab1, tab2 = st.tabs(["Process Single Request", "Batch Process Requests"])

with tab1:
    st.header("Process an HR Request")
    
    with st.form("hr_form"):
        col1, col2 = st.columns(2)
        with col1:
            request_id = st.text_input("Request ID", value="ONB-9000")
            employee_email = st.text_input("Employee Email", value="new.hire@company.com")
            department = st.selectbox("Department", ["engineering", "finance", "sales", "hr"])
            role = st.text_input("Role", value="senior_software_engineer")
        with col2:
            location = st.selectbox("Location", ["remote_us", "office_nyc", "office_sf"])
            systems = st.multiselect("Requested Systems", ["email", "slack", "github", "aws_console", "jira", "netsuite", "concur"], default=["email", "slack", "github"])
            user_query = st.text_area("Optional: Ask a Policy Question", value="What is the remote equipment stipend?")
            
        submitted = st.form_submit_button("Process Request", type="primary")

    if submitted:
        with st.spinner("Agent is analyzing the request..."):
            try:
                payload = {
                    "request_id": request_id,
                    "employee_email": employee_email,
                    "department": department,
                    "role": role,
                    "location": location,
                    "requested_systems": systems,
                    "user_query": user_query if user_query.strip() else None
                }
                response = requests.post(f"{API_URL}/process_request", json=payload)
                response.raise_for_status()
                data = response.json()
                
                if data.get("status") == "success":
                    result = data.get("result", {})
                    
                    st.subheader("Agent Outcome")
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Status", result.get("status", "Unknown").title())
                    col_b.metric("Risk Score", f"{result.get('risk_score', 0.0):.2f}")
                    col_c.metric("Trace ID", result.get("trace_id", "N/A").split("-")[1] if "-" in result.get("trace_id", "") else "N/A")
                    
                    if result.get("policy_context"):
                        st.info("💡 **Policy Answer:**\n" + result.get("policy_context"))
                        st.caption(f"Cited Version: {result.get('policy_version_cited')}")
                        
                    if result.get("checklist_items"):
                        st.write("### Onboarding Checklist")
                        for item in result.get("checklist_items", []):
                            st.checkbox(item, value=True, disabled=True)
                            
                    if result.get("provisioned_accounts"):
                        st.success(f"✅ Provisioned Systems: {', '.join(result.get('provisioned_accounts'))}")
                        
                    if result.get("error_log"):
                        st.error("⚠️ Errors/Blocks encountered:")
                        for err in result.get("error_log"):
                            st.write(f"- {err}")
                            
                    with st.expander("View Raw JSON Output"):
                        st.json(result)
                else:
                    st.error(f"Error processing request: {data.get('detail')}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

with tab2:
    st.header("Batch Process Mock Onboarding Requests")
    st.markdown("Run all test scenarios defined in `data/onboarding_requests.json` through the Agent.")
    
    if st.button("Run Batch Processor", type="primary"):
        with st.spinner("Processing batch... This may take a few moments."):
            try:
                response = requests.post(f"{API_URL}/requests/batch")
                response.raise_for_status()
                data = response.json()
                
                st.success(f"Successfully processed {data.get('processed')} requests!")
                
                for idx, res in enumerate(data.get("results", [])):
                    req_id = res.get("request_id")
                    status = res.get("status")
                    role = res.get("role")
                    
                    icon = "✅" if status in ["completed", "policy_qa"] else "⏳" if status == "needs_approval" else "⚠️"
                    
                    with st.expander(f"{icon} {req_id}: {role} ({status})"):
                        if res.get("user_query"):
                            st.write(f"**Query:** {res.get('user_query')}")
                        if res.get("policy_context"):
                            st.write("**Policy Q&A Answer:**")
                            st.info(res.get("policy_context"))
                        if res.get("provisioned_accounts"):
                            st.write(f"**Provisioned:** {', '.join(res.get('provisioned_accounts'))}")
                        if res.get("checklist_items"):
                            st.write(f"**Checklist:** {len(res.get('checklist_items'))} items generated.")
                        if res.get("error_log"):
                            st.error(f"Errors: {res.get('error_log')}")
                        
            except Exception as e:
                st.error(f"Failed to process batch: {e}")
