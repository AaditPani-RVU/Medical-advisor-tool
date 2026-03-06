"""
Chatbot UI Component using Streamlit Chat interface.
"""

import streamlit as st

def render_chat_page(api_post):
    """Render the chatbot assistant page."""
    
    st.title("💬 Health Assistant")
    
    st.markdown(
        """<div class="disclaimer-box">⚠️ <b>Educational content only.</b> 
        Not medical advice. If worried, seek professional care.</div>""",
        unsafe_allow_html=True,
    )

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi! I'm your Verified Health Assistant. How can I help you today? You can ask me questions, and I will find verified health information to answer you."}
        ]

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input
    if prompt := st.chat_input("Ask a health-related question... (e.g., 'What are the symptoms of diabetes?')"):
        # Add user message to state and display
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching verified sources..."):
                
                # We send the whole history
                request_payload = {
                    "messages": st.session_state.chat_messages
                }
                
                result = api_post("/chat", data=request_payload)
                
                if result:
                    answer = result.get("answer", "I could not find an answer.")
                    citations = result.get("citations", [])
                    grounded = result.get("grounded", False)
                    
                    st.markdown(answer)
                    
                    if not grounded:
                         st.warning("⚠️ This answer is not fully grounded in our verified knowledge base. It is generated using general medical knowledge.")
                         
                    if citations:
                        st.markdown("**Sources Used:**")
                        for ref in citations:
                            st.caption(f"- {ref.get('title')} ({ref.get('source_name')})")
                    
                    st.caption(result.get("disclaimer", ""))
                    
                    st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("Failed to get a response from the Chat API.")
