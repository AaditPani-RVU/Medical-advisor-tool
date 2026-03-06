"""
Triage questionnaire UI component — seek care guidance.
100% rule-based, no LLM involvement.
"""

import streamlit as st


def render_triage_page(api_get, api_post):
    """Render the triage questionnaire and results page."""

    st.info(
        "💡 **How this works:** Select a health topic, answer yes/no questions, "
        "and this tool will suggest a general urgency level based on rules "
        "from trusted public health sources (NHS, CDC, AHA). "
        "This is NOT a diagnosis."
    )

    # Get available topics
    topics_data = api_get("/triage/topics")
    if not topics_data:
        st.error("Could not load triage topics. Is the API running?")
        return

    available_topics = topics_data.get("topics", [])
    if not available_topics:
        st.warning("No triage topics configured.")
        return

    # Topic selection
    selected_topic = st.selectbox(
        "Select a health topic area",
        available_topics,
        format_func=lambda x: x.replace("-", " ").title(),
    )

    if not selected_topic:
        return

    # Get questions
    questions_data = api_get(f"/triage/questions/{selected_topic}")
    if not questions_data:
        st.error("Could not load questions.")
        return

    universal_qs = questions_data.get("universal_questions", [])
    topic_qs = questions_data.get("topic_questions", [])

    st.markdown("---")
    st.markdown("### ❓ Please answer the following questions")
    st.markdown("Answer honestly — this helps determine a general urgency level.")

    answers = {}

    # Universal red-flag questions
    if universal_qs:
        st.markdown("#### 🚩 General Safety Check")
        for q in universal_qs:
            answer = st.radio(
                q["text"],
                ["No", "Yes"],
                index=0,
                key=f"triage_{q['id']}",
                horizontal=True,
            )
            answers[q["id"]] = answer == "Yes"

    # Topic-specific questions
    if topic_qs:
        st.markdown(f"#### 📋 {selected_topic.replace('-', ' ').title()} Questions")
        for q in topic_qs:
            answer = st.radio(
                q["text"],
                ["No", "Yes"],
                index=0,
                key=f"triage_{q['id']}",
                horizontal=True,
            )
            answers[q["id"]] = answer == "Yes"

    st.markdown("---")

    # Run triage
    if st.button("🔍 Check Urgency Level", type="primary", use_container_width=True):
        result = api_post("/triage/run", {
            "topic": selected_topic,
            "answers": answers,
        })

        if result:
            _render_triage_result(result)


def _render_triage_result(result: dict):
    """Render the triage result with urgency level and specialist info."""
    urgency = result.get("urgency", "routine")
    message = result.get("message", "")
    source_refs = result.get("source_refs", [])
    specialist = result.get("specialist", {})

    st.markdown("---")
    st.markdown("### 📊 Result")

    # Urgency display
    if urgency == "emergency":
        st.markdown(
            f'<div class="urgency-emergency">'
            f'<h3>🔴 Urgent / Emergency</h3>'
            f'<p>{message}</p></div>',
            unsafe_allow_html=True,
        )
        st.error("⚡ If this is an emergency, call your local emergency number immediately.")
    elif urgency == "soon":
        st.markdown(
            f'<div class="urgency-soon">'
            f'<h3>🟡 See a Doctor Soon (within days)</h3>'
            f'<p>{message}</p></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="urgency-routine">'
            f'<h3>🟢 Routine Appointment / Monitor</h3>'
            f'<p>{message}</p></div>',
            unsafe_allow_html=True,
        )

    # Specialist suggestion
    if specialist:
        st.markdown("### 🩺 Suggested Specialist Type")
        st.markdown(
            "**Navigation only** — this does NOT mean you have a specific condition."
        )

        specialists_list = specialist.get("specialists", [])
        note = specialist.get("note", "")

        if specialists_list:
            for s in specialists_list:
                st.markdown(f"- **{s}**")
        if note:
            st.caption(note)

    # Source references
    if source_refs:
        st.markdown("### 📚 Sources")
        st.markdown("These urgency guidelines are based on information from:")
        for ref in source_refs:
            label = ref.get("label", "Source")
            url = ref.get("url", "")
            if url:
                st.markdown(f"- [{label}]({url})")
            else:
                st.markdown(f"- {label}")

    # Disclaimer
    st.markdown("---")
    st.warning(
        "⚠️ **Reminder:** This tool provides general guidance only, based on "
        "publicly available health information. It is NOT a substitute for "
        "professional medical evaluation. If you are concerned about your "
        "health, please consult a qualified healthcare professional."
    )
