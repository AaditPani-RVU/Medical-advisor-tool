"""
Family group management UI component.
"""

import streamlit as st


AVAILABLE_TOPICS = [
    "heart-health", "diabetes", "respiratory", "mental-health",
    "nutrition", "exercise-fitness", "sleep", "skin-conditions",
    "digestive-health", "thyroid", "bone-joint", "allergies",
    "eye-health", "ear-nose-throat", "dental-health",
    "womens-health", "mens-health", "child-health", "senior-health",
    "pregnancy", "immunization", "infectious-disease",
    "cancer-awareness", "chronic-pain", "first-aid", "general-wellness",
]


def render_family_page(api_get, api_post):
    """Render the family group management page."""

    tab_create, tab_manage = st.tabs(["➕ Create Group", "👥 Manage Groups"])

    # ── Tab: Create Group ──────────────────────────────────
    with tab_create:
        st.subheader("Create a Family Group")
        st.markdown("Create a family group to personalize content for your family members.")

        with st.form("create_group_form"):
            group_name = st.text_input("Group Name", placeholder="e.g., Smith Family")
            submitted = st.form_submit_button("Create Group")

            if submitted and group_name:
                result = api_post("/family/group", {"name": group_name})
                if result:
                    st.success(f"✅ Family group '{group_name}' created! (ID: {result['id']})")
                    st.session_state["active_group_id"] = result["id"]

        st.markdown("---")
        st.subheader("Add a Family Member")

        # Get groups for dropdown
        groups = api_get("/family/groups")
        if groups and len(groups) > 0:
            group_options = {g["name"]: g["id"] for g in groups}

            with st.form("add_member_form"):
                selected_group = st.selectbox(
                    "Family Group",
                    list(group_options.keys()),
                )
                member_name = st.text_input("Name (optional)", placeholder="e.g., Mom")
                age_band = st.selectbox("Age Band", ["adult", "kid", "teen", "senior"])

                st.markdown("**Content Preferences**")
                col1, col2 = st.columns(2)
                with col1:
                    content_format = st.selectbox("Preferred Format", ["all", "video", "text"])
                with col2:
                    length_pref = st.selectbox("Content Length", ["any", "short", "long"])

                language = st.text_input("Language", value="en")

                topics = st.multiselect(
                    "Topics of Interest",
                    AVAILABLE_TOPICS,
                    default=["general-wellness"],
                )

                member_submitted = st.form_submit_button("Add Member")

                if member_submitted:
                    group_id = group_options[selected_group]
                    data = {
                        "group_id": group_id,
                        "name": member_name,
                        "age_band": age_band,
                        "preferences": {
                            "content_format": content_format,
                            "language": language,
                            "length_preference": length_pref,
                        },
                        "topics": topics,
                    }
                    result = api_post("/family/member", data)
                    if result:
                        st.success(f"✅ Member '{member_name or 'Unnamed'}' added!")
        else:
            st.info("Create a family group first to add members.")

    # ── Tab: Manage Groups ─────────────────────────────────
    with tab_manage:
        st.subheader("Your Family Groups")

        groups = api_get("/family/groups")
        if not groups or len(groups) == 0:
            st.info("No family groups yet. Create one in the Create Group tab.")
            return

        for group in groups:
            with st.expander(f"👨‍👩‍👧‍👦 {group['name']} (ID: {group['id']})"):
                detail = api_get(f"/family/group/{group['id']}")
                if detail:
                    members = detail.get("members", [])
                    if members:
                        for member in members:
                            col1, col2, col3 = st.columns([2, 1, 2])
                            with col1:
                                st.markdown(f"**{member.get('name') or 'Unnamed'}**")
                            with col2:
                                st.caption(f"Age: {member.get('age_band', 'N/A')}")
                            with col3:
                                topics = member.get("topics", [])
                                if topics:
                                    st.caption(f"Topics: {', '.join(topics[:3])}")
                    else:
                        st.caption("No members yet.")

                    # Set as active group
                    if st.button(
                        f"Set as active group",
                        key=f"activate_{group['id']}",
                    ):
                        st.session_state["active_group_id"] = group["id"]
                        st.success(f"Active group set to: {group['name']}")
