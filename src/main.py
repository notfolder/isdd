import streamlit as st
from core.data_handler import DataHandler
from engine.statistics import StatisticsEngine
from visualization.plotter import VisualizationManager
import sys
import os

# Ensure the src directory is in python path for imports to work correctly.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class AppMain:
    """
    Controller for the application. Manages UI state and orchestrates
    the interaction between different modules.
    """

    def __init__(self):
        # Initialize services/engines according to design doc structure
        self.data_handler = DataHandler()
        self.statistics_engine = StatisticsEngine()
        self.visualization_manager = VisualizationManager()

    def run(self):
        # Initialize session state if not present
        if "page" not in st.session_state:
            st.session_state["page"] = "upload"

        if st.session_state["page"] == "results":
            self._show_results()
        else:
            self._show_upload_screen()

    def _show_upload_screen(self):
        st.title("Σ Sigma Plot & Distribution Comparison")
        st.write("Upload a CSV file to get started.")

        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

        if uploaded_file is not None:
            # Handle data loading and storage in session state
            if "df" not in st.session_state:
                try:
                    # Load the data using DataHandler
                    df = self.data_handler.load_csv(uploaded_file)
                    st.session_state["df"] = df
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                # Re-uploading updates the current session data to match new file
                try:
                    df = self.data_handler.load_csv(uploaded_file)
                    st.session_state["df"] = df
                except Exception as e:
                    st.error(f"Error: {e}")

            # If data is successfully loaded, show configuration options (Column Selection)
            if "df" in st.session_state:
                st.divider()
                st.subheader("Configuration")
                df = st.session_state["df"]
                columns = self.data_handler.get_column_names(df)

                col1, col2 = st.columns(2)
                with col1:
                    column_a = st.selectbox(
                        "Select Column A (Variable X)",
                        columns,
                        index=0 if len(columns) > 0 else None,
                        key="col_a",
                    )
                with col2:
                    column_b = st.selectbox(
                        "Select Column B (Variable Y)",
                        columns,
                        index=1 if len(columns) > 1 else None,
                        key="col_b",
                    )

                if st.button("Run Analysis", type="primary", use_container_width=True):
                    # Basic validation: check if columns are valid and numeric before proceeding
                    if self.data_handler.validate_numeric_columns(
                        df, [column_a, column_b]
                    ):
                        st.session_state["selected_col_a"] = column_a
                        st.session_state["selected_col_b"] = column_b
                        st.session_state["page"] = "results"
                        st.rerun()
                    else:
                        st.error("Please select two valid numeric columns.")

            else:
                st.info("Please upload a CSV file to proceed.")

    def _show_results(self):
        st.title("Analysis Results")
        df = st.session_state["df"]
        col_a_name = st.session_state.get("selected_col_a")
        col_b_name = st.session_state.get("selected_col_b")

        # UI Controls (Top Row)
        ctrl1, ctrl2 = st.columns([3, 1])
        with ctrl2:
            if st.button("Back to Upload", use_container_width=True):
                st.session_state["page"] = "upload"
                # Clear session state to allow re-uploads
                if "df" in st.session_state:
                    del st.session_state["df"]
                st.rerun()
            if st.button("Reset Everything", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        if not col_a_name or not col_b_name:
            st.warning("Analysis parameters missing in session state.")
            if st.button("Return to Upload Screen"):
                st.session_state["page"] = "upload"
                if "df" in st.session_state:
                    del st.session_state["df"]
                st.rerun()
            return

        with ctrl1:
            st.caption(f"Analyzing: {col_a_name} vs {col_b_name}")

        st.divider()

        # 1. Histograms (Two side-by-side columns)
        hist_col1, hist_col2 = st.columns(2)

        # Calculate histogram data using StatisticsEngine logic paths
        hist_data_a = self.statistics_engine.calculate_histogram(df, col_a_name)
        hist_data_b = self.statistics_engine.calculate_histogram(df, col_b_name)

        # Generate and show plots using VisualizationManager objects
        fig_a = self.visualization_manager.generate_histogram(
            hist_data_a, title=f"Histogram: {col_a_name}"
        )
        fig_b = self.visualization_manager.generate_histogram(
            hist_data_b, title=f"Histogram: {col_b_name}"
        )

        with hist_col1:
            st.pyplot(fig_a)

        with hist_col2:
            st.pyplot(fig_b)

        st.divider()

        # 2. Q-Q Plot (Full width focus)
        st.subheader("Comparison: Quantile-Quantile Analysis")
        qq_data = self.statistics_engine.calculate_qq_plot_data(
            df, col_a_name, col_b_name
        )
        if qq_data:
            fig_qq = self.visualization_manager.generate_qq_plot(qq_data[0], qq_data[1])
            st.pyplot(fig_qq)
        else:
            st.error("Could not generate Q-Q plot data.")


def main():
    # Page configuration (must be first in Streamlit)
    st.set_page_config(page_title="Sigma Plot Web App", layout="wide")

    # Initialize application controller instance and run the loop logic.
    app = AppMain()
    app.run()


if __name__ == "__main__":
    main()
