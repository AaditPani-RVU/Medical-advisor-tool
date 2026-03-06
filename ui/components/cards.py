"""
Content card and proof-of-trust card UI components.
"""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000"


def render_content_card(item: dict, show_save: bool = False):
    """Render a content item card with trust badge and summary."""
    with st.container():
        st.markdown("---")

        # Header row
        col_title, col_badge = st.columns([4, 1])
        with col_title:
            is_insta = item.get("type") == "instagram_reel" or "instagram.com" in item.get('url', '')
            if is_insta:
                icon = "📱"
            else:
                icon = "🎬" if item.get("type") in ("video", "short_video") else "📄"

            st.markdown(f"### {icon} {item.get('title', 'Untitled')}")
        with col_badge:
            tier = item.get("source_tier", "")
            if tier == "verified_org":
                st.markdown(
                    '<span class="trust-badge-org">✅ Verified Org</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<span class="trust-badge-creator">🔵 Verified Creator</span>',
                    unsafe_allow_html=True,
                )

        # Source info
        is_insta = item.get("type") == "instagram_reel" or "instagram.com/reel" in item.get('url', '')
        is_shorts = "youtube.com/shorts" in item.get('url', '')
        if is_insta or is_shorts or item.get('type') == 'short_video':
            display_type = "Instagram Reel" if is_insta else "Short-form (Reel/Shorts)"
        else:
            display_type = item.get('type', 'article').title()

        # Show creator handle for Instagram reels
        source_display = item.get('source_name', 'Unknown')
        if is_insta and not source_display.startswith("@"):
            source_display = f"@{source_display}" if source_display else "Unknown"
        
        st.caption(
            f"**Source:** {source_display} · "
            f"**Published:** {item.get('published_at', 'N/A')} · "
            f"**Type:** {display_type}"
        )
        # Deterministic Reliability Score (Max 100) based on strict metadata
        score = 0
        
        # 1. Source Tier Base (max 50)
        tier = item.get("source_tier", "")
        if tier == "verified_org":
            score += 50
        elif tier == "verified_creator":
            score += 40
            
        # 2. Content Length/Depth (max 20)
        length = item.get("content_length", 0)
        if length >= 2000:       # Long article (~400 words) or long video
            score += 20
        elif length >= 500:      # Standard
            score += 15
        elif length > 0:         # Short
            score += 10
        else:                    # No text/transcript available (e.g. some Reels)
            score += 10 
            
        # 3. Medical Specificity / Tags (max 15)
        # We assume empty tags or generic tags like 'general-wellness' are less specific 
        # than explicitly extracted medical conditions.
        tags = item.get("tags", [])
        medical_tags = [t for t in tags if t not in ("general-wellness",)]
        if len(medical_tags) >= 2:
            score += 15
        elif len(medical_tags) == 1:
            score += 10
        else:
            score += 5
            
        # 4. Recency (max 15)
        published_at = item.get("published_at")
        if published_at:
            try:
                from datetime import datetime
                # Parse ISO format (handling Z timezone)
                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                # Assuming current year is ~2026 based on mock, but using basic year math
                now_year = datetime.now().year
                age_years = now_year - pub_date.year
                
                if age_years == 0:
                    score += 15
                elif age_years == 1:
                    score += 10
                else:
                    score += 5
            except:
                score += 5
        else:
            score += 5

        # Cap at 100 just to be safe
        score = min(100, score)
        
        st.caption(f"🛡️ **Reliability Score: {score}/100** *(Deterministically calculated)*")


        # Summary
        summary = item.get("summary", {})
        if isinstance(summary, dict) and summary.get("summary"):
            st.markdown(f"_{summary['summary']}_")

            key_points = summary.get("key_points", [])
            if key_points:
                with st.expander("Key points covered"):
                    for kp in key_points:
                        st.markdown(f"- {kp}")

            warnings = summary.get("warnings", [])
            if warnings and any(w for w in warnings):
                with st.expander("⚠️ Content notes"):
                    for w in warnings:
                        if w:
                            st.warning(w)

        # Tags
        tags = item.get("tags", [])
        if tags:
            tag_str = " ".join([f"`{t}`" for t in tags])
            st.markdown(f"**Topics:** {tag_str}")

        # Action row & Video Embedding
        url = item.get("url", "")
        if url:
            st.markdown(f"[🔗 View original source]({url})")
            
            # Show Instagram Reel embed if applicable
            if "instagram.com/reel" in url:
                with st.expander("🎥 Watch Reel"):
                    # Instagram embed URL format is usually exact reel URL + embed feature
                    embed_url = url.rstrip('/') + "/embed"
                    st.components.v1.iframe(embed_url, width=400, height=480, scrolling=True)
            # Alternatively, if it's a YouTube video
            elif "youtube.com" in url or "youtu.be" in url:
                with st.expander("🎥 Watch Video"):
                    st.video(url)
