import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from ui.state import save_persisted_state


def show_signal_history():
    st.header("Signal History")

    if st.session_state.signals_history:
        # Convert to DataFrame
        df = pd.DataFrame(st.session_state.signals_history)

        # Filters
        col1, col2, col3 = st.columns(3)

        with col1:
            symbol_filter = st.selectbox(
                "Filter by Symbol",
                ["All"] + list(df['symbol'].unique())
            )

        with col2:
            signal_filter = st.selectbox(
                "Filter by Signal",
                ["All", "BUY", "SELL"]
            )

        with col3:
            days_filter = st.selectbox(
                "Filter by Days",
                ["All", "Last 7 days", "Last 30 days"]
            )

        # Apply filters
        filtered_df = df.copy()

        if symbol_filter != "All":
            filtered_df = filtered_df[filtered_df['symbol'] == symbol_filter]

        if signal_filter != "All":
            filtered_df = filtered_df[filtered_df['signal'] == signal_filter]

        if days_filter == "Last 7 days":
            cutoff_date = datetime.now() - timedelta(days=7)
            filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff_date]
        elif days_filter == "Last 30 days":
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_df = filtered_df[filtered_df['timestamp'] >= cutoff_date]

        # Display filtered results
        if not filtered_df.empty:
            st.dataframe(filtered_df, use_container_width=True)

            # Export functionality
            if st.button("📥 Export to CSV"):
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"trading_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.info("No signals match the selected filters.")

        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.signals_history = []
            save_persisted_state()
            st.success("Signal history cleared!")
            st.rerun()

    else:
        st.info("No signal history available. Signals will appear here as they are generated.")
