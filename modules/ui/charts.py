import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def render_radar_chart(categories: list, values: list, title: str = "Audience DNA"):
    """
    Renders a Radar Chart for Audience Personality.
    """
    fig = go.Figure(data=go.Scatterpolar(
      r=values,
      theta=categories,
      fill='toself',
      line_color='#10b981',
      fillcolor='rgba(16, 185, 129, 0.2)'
    ))

    fig.update_layout(
      polar=dict(
        radialaxis=dict(
          visible=True,
          range=[0, 100],
          showticklabels=False,
          gridcolor='rgba(255,255,255,0.1)'
        ),
        bgcolor='rgba(0,0,0,0)'
      ),
      paper_bgcolor='rgba(0,0,0,0)',
      font=dict(color='white'),
      margin=dict(l=40, r=40, t=40, b=40),
      showlegend=False,
      height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_comparison_radar(categories: list, series: list[dict]):
    """
    Renders a multi-series Radar Chart for comparison.
    series = [{'name': 'Creator A', 'values': [80, 50...], 'color': '#...'}, ...]
    """
    fig = go.Figure()
    
    for s in series:
        fig.add_trace(go.Scatterpolar(
            r=s['values'],
            theta=categories,
            fill='toself',
            name=s['name'],
            line_color=s.get('color', '#10b981'),
            opacity=0.6
        ))

    fig.update_layout(
      polar=dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(255,255,255,0.2)'),
        bgcolor='rgba(0,0,0,0)'
      ),
      paper_bgcolor='rgba(0,0,0,0)',
      font=dict(color='white'),
      margin=dict(l=40, r=40, t=20, b=20),
      legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
      height=350
    )
    st.plotly_chart(fig, use_container_width=True)

def render_trend_line(history: list):
    """
    Renders a Score Trend Line.
    history: List of AnalysisRun objects.
    """
    if not history:
        return
        
    data = []
    for run in history:
        # Clean date
        date_str = run.created_at[:10] if run.created_at else "Unknown"
        data.append({"Date": date_str, "Score": run.fit_score})
    
    # Sort by date (oldest first for trend)
    data = sorted(data, key=lambda x: x['Date'])
    df = pd.DataFrame(data)
    
    fig = px.line(df, x="Date", y="Score", markers=True)
    fig.update_traces(line_color='#3b82f6', line_width=3)
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.1)'),
        xaxis=dict(showgrid=False),
        margin=dict(l=20, r=20, t=20, b=20),
        height=200
    )
    st.plotly_chart(fig, use_container_width=True)
