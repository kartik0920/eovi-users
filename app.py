import streamlit as st
import pandas as pd
import streamlit_authenticator as stauth
from yaml import safe_load
from supabase import create_client
from dotenv import load_dotenv
import os
import math

# ------------------ LOAD ENV --------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------ AUTH --------------------
with open("credentials.yaml") as file:
    config = safe_load(file)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

authenticator.login(location="main")

# ------------------ AUTH LOGIC --------------------
if st.session_state["authentication_status"]:
    authenticator.logout("Logout", "sidebar")
    st.title("👤 Users Dashboard")
    st.write(f"Welcome, {st.session_state['name']}!")

    # Create tabs
    tab1, tab2 = st.tabs(["Users", "📈 Metrics"])

    with tab1:
        limit = 10
        total_users = (
            supabase.table("users_table")
            .select("*", count="exact", head=True)
            .execute()
        )
        total_count = total_users.count or 0
        total_pages = math.ceil(total_count / limit)

        if "page" not in st.session_state:
            st.session_state.page = 1

        page = st.session_state.page
        start_index = (page - 1) * limit
        end_index = start_index + limit - 1

        data = (
            supabase.table("users_table")
            .select("*")
            .range(start_index, end_index)
            .execute()
        )

        if data.data:
            st.dataframe(data.data)
        else:
            st.info("No users found.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⬅️ Previous", disabled=page == 1):
                st.session_state.page -= 1
                st.experimental_rerun()
        with col2:
            st.write(f"Page {page} of {total_pages}")
        with col3:
            if st.button("Next ➡️", disabled=page == total_pages):
                st.session_state.page += 1
                st.experimental_rerun()

    # ------------------ Metrics Tab (MAU / DAU) ------------------
    with tab2:
        st.subheader("📊 User Metrics Overview")

        # Fetch MAU and DAU data from Supabase daily_metric table
        response = (
            supabase.table("daily_metrics")
            .select("metric_date, dau, mau")
            .order("metric_date")
            .execute()
        )

        if response.data:
            # Convert to DataFrame
            df = pd.DataFrame(response.data)
            df["metric_date"] = pd.to_datetime(
                df["metric_date"]
            )  # convert date strings to datetime objects

            st.markdown("#### Daily Active Users (DAU)")
            st.line_chart(df, x="metric_date", y="dau")

            st.markdown("#### Monthly Active Users (MAU)")
            st.line_chart(df, x="metric_date", y="mau")
        else:
            st.info("No metrics data found.")


elif st.session_state["authentication_status"] is False:
    st.error("Incorrect username or password")

elif st.session_state["authentication_status"] is None:
    st.warning("Please enter your username and password")
