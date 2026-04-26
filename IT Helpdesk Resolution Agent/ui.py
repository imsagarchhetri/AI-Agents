import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="IT Helpdesk AI Agent", page_icon="🤖", layout="wide")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("🤖 Agentic IT Helpdesk")
st.markdown("An AI-powered IT Support Agent built with LangGraph.")

tab1, tab2 = st.tabs(["Single Ticket Processing", "Batch Processing"])

with tab1:
    st.header("Process a Support Ticket")
    
    with st.form("ticket_form"):
        col1, col2 = st.columns([1, 3])
        with col1:
            ticket_id = st.text_input("Ticket ID", value="INC-2048")
        with col2:
            description = st.text_area("Ticket Description", value="Cannot connect to office WiFi. Device shows 'Authentication Failed'. Tried rebooting.")
        
        submitted = st.form_submit_button("Process Ticket", type="primary")

    if submitted:
        if not ticket_id or not description:
            st.error("Please provide both a Ticket ID and Description.")
        else:
            with st.spinner("Agent is analyzing the ticket..."):
                try:
                    payload = {"ticket_id": ticket_id, "description": description}
                    response = requests.post(f"{API_URL}/process_ticket", json=payload)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("status") == "success":
                        result = data.get("result", {})
                        
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric("Category", result.get("category", "Unknown").title())
                        col_b.metric("Priority", result.get("priority", "Unknown").title())
                        col_c.metric("Status", result.get("status", "Unknown").title())
                        
                        st.subheader("Resolution Plan")
                        plan = result.get("resolution_plan") or result.get("diagnostic_result") or "No plan generated."
                        st.info(plan)
                        
                        kb = result.get("kb_context")
                        if kb:
                            with st.expander("View Knowledge Base Article Used"):
                                st.markdown(kb)
                                
                        with st.expander("View Raw JSON Output"):
                            st.json(result)
                    else:
                        st.error(f"Error processing ticket: {data.get('detail')}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")

with tab2:
    st.header("Batch Process Mock Tickets")
    st.markdown("Run all test scenarios defined in `data/it_tickets.json` through the Agent.")
    
    if st.button("Run Batch Processor", type="primary"):
        with st.spinner("Processing batch... This may take a minute as it queries the LLM for multiple tickets."):
            try:
                response = requests.post(f"{API_URL}/tickets/batch")
                response.raise_for_status()
                data = response.json()
                
                st.success(f"Successfully processed {data.get('processed')} tickets!")
                
                for idx, res in enumerate(data.get("results", [])):
                    ticket_id = res.get("ticket_id")
                    ticket_res = res.get("result", {})
                    status = ticket_res.get("status")
                    
                    # Pick an icon based on status
                    icon = "✅" if status == "resolved" else "⏳" if status == "needs_approval" else "⚠️"
                    
                    with st.expander(f"{icon} {ticket_id}: {ticket_res.get('category', 'unknown').title()} Issue"):
                        st.write(f"**Description:** {ticket_res.get('raw_description')}")
                        st.write(f"**Status:** `{status}`")
                        st.write(f"**Action/Plan:**")
                        st.info(ticket_res.get("resolution_plan") or ticket_res.get("diagnostic_result") or "Waiting for Human Approval / Escalation.")
                        
            except Exception as e:
                st.error(f"Failed to process batch: {e}")
