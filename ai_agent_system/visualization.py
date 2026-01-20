"""
Data Visualization Helper
Handles chart creation for CSV data
Company: Sepia ML | Developer: Shreyash Shankarrao Jadhav
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from typing import List, Optional


class DataVisualizer:
    """Create visualizations from query results"""
    
    @staticmethod
    def create_chart(df: pd.DataFrame, chart_type: str, 
                     x_col: Optional[str] = None,
                     y_cols: Optional[List[str]] = None):
        """
        Create chart with proper validation
        
        Args:
            df: DataFrame with query results
            chart_type: 'bar', 'line', or 'pie'
            x_col: X-axis column (optional for auto-select)
            y_cols: Y-axis columns (optional for auto-select)
        """
        try:
            if df.empty:
                st.warning("No data to visualize")
                return
            
            # Get numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                st.error("No numeric columns found for visualization")
                return
            
            # If columns not specified, let user select
            if not x_col or not y_cols:
                st.write("**Select columns for visualization:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    x_col = st.selectbox("X-axis (Category)", df.columns.tolist(), key=f"x_{chart_type}")
                
                with col2:
                    if chart_type == "pie":
                        y_cols = [st.selectbox("Value column", numeric_cols, key=f"y_{chart_type}")]
                    else:
                        y_cols = st.multiselect("Y-axis (Values)", numeric_cols, 
                                               default=numeric_cols[:1], key=f"y_{chart_type}")
            
            if not y_cols:
                st.warning("Please select at least one value column")
                return
            
            # Create chart based on type
            if chart_type == "bar":
                DataVisualizer._create_bar_chart(df, x_col, y_cols)
            elif chart_type == "line":
                DataVisualizer._create_line_chart(df, x_col, y_cols)
            elif chart_type == "pie":
                DataVisualizer._create_pie_chart(df, x_col, y_cols[0])
        
        except Exception as e:
            st.error(f"Visualization failed: {e}")
            print(f"❌ Chart creation error: {e}")
    
    @staticmethod
    def _create_bar_chart(df: pd.DataFrame, x_col: str, y_cols: List[str]):
        """Create bar chart"""
        try:
            # Validate y_cols are numeric
            valid_y_cols = [col for col in y_cols if col in df.select_dtypes(include=['number']).columns]
            
            if not valid_y_cols:
                st.error("Selected columns are not numeric")
                return
            
            # Limit rows for readability
            if len(df) > 50:
                st.info(f"Showing top 50 of {len(df)} rows")
                df = df.head(50)
            
            # Create figure
            if len(valid_y_cols) == 1:
                fig = px.bar(
                    df,
                    x=x_col,
                    y=valid_y_cols[0],
                    title=f"{valid_y_cols[0]} by {x_col}",
                    labels={x_col: x_col, valid_y_cols[0]: valid_y_cols[0]}
                )
            else:
                fig = px.bar(
                    df,
                    x=x_col,
                    y=valid_y_cols,
                    title=f"Comparison by {x_col}",
                    barmode='group'
                )
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title="Value",
                hovermode='x unified',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Bar chart error: {e}")
    
    @staticmethod
    def _create_line_chart(df: pd.DataFrame, x_col: str, y_cols: List[str]):
        """Create line chart"""
        try:
            valid_y_cols = [col for col in y_cols if col in df.select_dtypes(include=['number']).columns]
            
            if not valid_y_cols:
                st.error("Selected columns are not numeric")
                return
            
            if len(valid_y_cols) == 1:
                fig = px.line(
                    df,
                    x=x_col,
                    y=valid_y_cols[0],
                    title=f"{valid_y_cols[0]} over {x_col}",
                    markers=True
                )
            else:
                fig = px.line(
                    df,
                    x=x_col,
                    y=valid_y_cols,
                    title=f"Trends over {x_col}",
                    markers=True
                )
            
            fig.update_layout(
                xaxis_title=x_col,
                yaxis_title="Value",
                hovermode='x unified',
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Line chart error: {e}")
    
    @staticmethod
    def _create_pie_chart(df: pd.DataFrame, x_col: str, y_col: str):
        """Create pie chart"""
        try:
            if y_col not in df.select_dtypes(include=['number']).columns:
                st.error(f"Column '{y_col}' is not numeric")
                return
            
            # Aggregate if needed
            if len(df) > 20:
                st.info("Aggregating data for pie chart (showing top 20)")
                df_agg = df.groupby(x_col)[y_col].sum().reset_index()
                df_agg = df_agg.nlargest(20, y_col)
            else:
                df_agg = df[[x_col, y_col]]
            
            fig = px.pie(
                df_agg,
                names=x_col,
                values=y_col,
                title=f"Distribution of {y_col} by {x_col}"
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            
            st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Pie chart error: {e}")
    
    @staticmethod
    def show_data_table(df: pd.DataFrame, title: str = "Query Results"):
        """Display data as formatted table"""
        try:
            st.subheader(title)
            
            # Show row count
            st.caption(f"📊 {len(df)} rows × {len(df.columns)} columns")
            
            # Display dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=False
            )
        
        except Exception as e:
            st.error(f"Table display error: {e}")