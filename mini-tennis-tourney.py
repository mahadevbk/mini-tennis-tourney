import streamlit as st
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register a custom font (for example, 'Arial')
pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))  #  Make sure 'Arial.ttf' is in the same directory or specify the correct path.

def generate_tournament_layout(num_teams, num_courts):
    """
    Generates the layout for a tennis tournament, including team assignments,
    semi-final pairings, and the final match.  Handles edge cases and errors.

    Args:
        num_teams (int): The number of teams participating in the tournament.
        num_courts (int): The number of tennis courts available.

    Returns:
        tuple: A tuple containing the following:
            - team_assignments (dict): A dictionary mapping court numbers to lists of teams.
            - semi_final_pairings (list): A list of tuples, where each tuple represents a semi-final pairing.
            - final_pairing (tuple): A tuple representing the final match pairing.
            - error_message (str): An error message if any error occurs, otherwise None.
    """
    error_message = None
    team_assignments = {}
    semi_final_pairings = []
    final_pairing = ()

    if not 8 <= num_teams <= 16:
        error_message = "Number of teams must be between 8 and 16."
        return team_assignments, semi_final_pairings, final_pairing, error_message
    if not 2 <= num_courts <= 4:
        error_message = "Number of courts must be between 2 and 4."
        return team_assignments, semi_final_pairings, final_pairing, error_message
    if num_teams % num_courts != 0:
        error_message = "Number of teams must be divisible by the number of courts."
        return team_assignments, semi_final_pairings, final_pairing, error_message

    teams = [f"Team {i+1}" for i in range(num_teams)]
    random.shuffle(teams)

    teams_per_court = num_teams // num_courts
    for court in range(1, num_courts + 1):
        team_assignments[court] = teams[(court - 1) * teams_per_court : court * teams_per_court]

    # Determine semi-final pairings (top team from each court)
    semi_final_teams = [team_assignments[court][0] for court in range(1, num_courts + 1)] # simplified to pick first team
    if num_courts == 2:
        semi_final_pairings = [(semi_final_teams[0], semi_final_teams[1])]
        final_pairing = (semi_final_teams[0], semi_final_teams[1]) # simplified
    elif num_courts == 3:
        semi_final_pairings = [(semi_final_teams[0], semi_final_teams[1]), (semi_final_teams[2], "Bye")] #simplified
        final_pairing = (semi_final_teams[0], semi_final_teams[1])
    elif num_courts == 4:
        semi_final_pairings = [(semi_final_teams[0], semi_final_teams[1]), (semi_final_teams[2], semi_final_teams[3])]
        final_pairing = (semi_final_teams[0], semi_final_teams[2]) # simplified.

    return team_assignments, semi_final_pairings, final_pairing, error_message



def create_pdf_layout(team_assignments, semi_final_pairings, final_pairing, num_courts):
    """
    Creates a PDF document outlining the tournament layout.

    Args:
        team_assignments (dict): A dictionary mapping court numbers to lists of teams.
        semi_final_pairings (list): A list of tuples, where each tuple represents a semi-final pairing.
        final_pairing (tuple): A tuple representing the final match pairing.
        num_courts (int): Number of courts.

    Returns:
        BytesIO: A BytesIO object containing the PDF data.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    # Use the custom font
    styles['Normal'].fontName = 'Arial'
    styles['Heading1'].fontName = 'Arial'
    styles['Heading2'].fontName = 'Arial'
    styles['Heading3'].fontName = 'Arial'

    # Title of the tournament
    title = Paragraph("Tennis Tournament Layout", styles['Heading1'])
    title.style.alignment = 1  # Center alignment
    elements.append(title)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))  # Add spacing

    # Team Assignments Table
    elements.append(Paragraph("Team Assignments:", styles['Heading2']))
    data = [["Court", "Teams"]]
    for court, teams in team_assignments.items():
        data.append([f"Court {court}", ", ".join(teams)])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#4a148c'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Arial'),  # Set font for the table
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, '#000000'),
    ]))
    elements.append(table)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

     # Semi-Final Pairings
    elements.append(Paragraph("Semi-Final Pairings:", styles['Heading2']))
    if semi_final_pairings:
        data_semi = [["Court", "Team 1", "Team 2"]]
        for i, (team1, team2) in enumerate(semi_final_pairings):
             data_semi.append([f"Court {i+1}", team1, team2])
        table_semi = Table(data_semi)
        table_semi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#003366'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),  # Set font
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ]))
        elements.append(table_semi)
    else:
        elements.append(Paragraph("N/A", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Final Pairing
    elements.append(Paragraph("Final Pairing:", styles['Heading2']))
    if final_pairing:
        data_final = [["Team 1", "Team 2"]]
        data_final.append([final_pairing[0], final_pairing[1]])
        table_final = Table(data_final)
        table_final.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#990000'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),  # Set font
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ]))
        elements.append(table_final)
    else:
        elements.append(Paragraph("N/A", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
def main():
    """
    Main function to run the Streamlit application.
    """
    st.title("Tennis Tournament Generator")

    num_teams = st.number_input("Number of Teams (8-16):", min_value=8, max_value=16, value=8)
    num_courts = st.number_input("Number of Courts (2-4):", min_value=2, max_value=4, value=2)

    if st.button("Generate Tournament"):
        team_assignments, semi_final_pairings, final_pairing, error_message = generate_tournament_layout(num_teams, num_courts)

        if error_message:
            st.error(error_message)
        else:
            st.success("Tournament layout generated successfully!")
            pdf_buffer = create_pdf_layout(team_assignments, semi_final_pairings, final_pairing, num_courts)
            st.download_button(
                label="Download Tournament Layout (PDF)",
                data=pdf_buffer,
                file_name="tournament_layout.pdf",
                mime="application/pdf",
            )

            # Display the generated layout (optional, for visual confirmation in the app)
            st.subheader("Team Assignments:")
            for court, teams in team_assignments.items():
                st.write(f"Court {court}: {', '.join(teams)}")

            st.subheader("Semi-Final Pairings:")
            if semi_final_pairings:
                for pairing in semi_final_pairings:
                    st.write(f"{pairing[0]} vs {pairing[1]}")
            else:
                st.write("N/A")

            st.subheader("Final Pairing:")
            if final_pairing:
                st.write(f"{final_pairing[0]} vs {final_pairing[1]}")
            else:
                st.write("N/A")

if __name__ == "__main__":
    main()
