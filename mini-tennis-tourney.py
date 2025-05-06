import streamlit as st
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a custom font
pdfmetrics.registerFont(TTFont('Arial', 'CoveredByYourGrace-Regular.ttf'))

def generate_tournament_layout(num_teams, num_courts):
    """
    Generates the layout for a tennis tournament, including team assignments.

    Args:
        num_teams (int): The number of teams participating in the tournament.
        num_courts (int): The number of tennis courts available.

    Returns:
        tuple: A tuple containing the following:
            - team_assignments (dict): A dictionary mapping court numbers to lists of teams.
            - error_message (str): An error message if any error occurs, otherwise None.
    """
    error_message = None
    team_assignments = {}

    if not 8 <= num_teams <= 16:
        error_message = "Number of teams must be between 8 and 16."
        return team_assignments, error_message
    if not 2 <= num_courts <= 4:
        error_message = "Number of courts must be between 2 and 4."
        return team_assignments, error_message

    teams = [f"Team {i+1}" for i in range(num_teams)]
    random.shuffle(teams)

    teams_per_court = num_teams // num_courts
    remaining_teams = num_teams % num_courts

    for court in range(1, num_courts + 1):
        court_teams = teams[(court - 1) * teams_per_court : court * teams_per_court]
        if remaining_teams > 0:
            court_teams.append(teams[num_teams - remaining_teams])
            remaining_teams -= 1
        team_assignments[court] = court_teams

    return team_assignments, error_message


def create_pdf_layout(team_assignments, num_courts):
    """
    Creates a PDF document outlining the tournament layout.

    Args:
        team_assignments (dict): A dictionary mapping court numbers to lists of teams.
        num_courts (int): Number of courts.

    Returns:
        BytesIO: A BytesIO object containing the PDF data.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Arial'
    styles['Heading1'].fontName = 'Arial'
    styles['Heading2'].fontName = 'Arial'
    styles['Heading3'].fontName = 'Arial'

    # Title
    title = Paragraph("Tennis Tournament Layout", styles['Heading1'])
    title.style.alignment = 1
    elements.append(title)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Team Assignments
    elements.append(Paragraph("Team Assignments:", styles['Heading2']))
    data = [["Court", "Teams"]]
    for court, teams in team_assignments.items():
        data.append([f"Court {court}", ", ".join(teams)])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#4a148c'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer



def main():
    """
    Main function to run the Streamlit application.
    """
    st.title("Tennis Tournament Generator")

    # Initialize session state variables
    if 'generate_tournament' not in st.session_state:
        st.session_state.generate_tournament = False
    if 'team_assignments' not in st.session_state:
        st.session_state.team_assignments = {}
    if 'num_courts' not in st.session_state:
        st.session_state.num_courts = 0
    if 'num_teams' not in st.session_state:
        st.session_state.num_teams = 0

    num_teams = st.number_input("Number of Teams (8-16):", min_value=8, max_value=16, value=8)
    num_courts = st.number_input("Number of Courts (2-4):", min_value=2, max_value=4, value=2)
    
    st.session_state.num_courts = num_courts
    st.session_state.num_teams = num_teams

    if st.button("Generate Tournament"):
        st.session_state.generate_tournament = True
        team_assignments, error_message = generate_tournament_layout(num_teams, num_courts)
        if error_message:
            st.error(error_message)
            st.session_state.generate_tournament = False # added to prevent errors
        else:
            st.session_state.team_assignments = team_assignments

    if st.session_state.generate_tournament:
        team_assignments = st.session_state.get("team_assignments", {})
        if not team_assignments:
            st.stop()
        st.success("Tournament layout generated successfully!")
        
        pdf_buffer = create_pdf_layout(team_assignments, num_courts)
        st.download_button(
            label="Download Tournament Layout (PDF)",
            data=pdf_buffer,
            file_name="tournament_layout.pdf",
            mime="application/pdf",
        )

        # Display layout in Streamlit
        st.subheader("Team Assignments:")
        for court, teams in team_assignments.items():
            st.write(f"Court {court}: {', '.join(teams)}")
if __name__ == "__main__":
    main()
