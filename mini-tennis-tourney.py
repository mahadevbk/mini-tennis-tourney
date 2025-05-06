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



def determine_semi_finals(court_winners):
    """
    Determines the semi-final pairings based on the winners of each court.

    Args:
        court_winners (list): A list of the winning teams from each court.

    Returns:
        list: A list of tuples, where each tuple represents a semi-final pairing.
    """
    semi_final_pairings = []
    if len(court_winners) == 2:
        semi_final_pairings = [(court_winners[0], court_winners[1])]
    elif len(court_winners) == 3:
        semi_final_pairings = [(court_winners[0], court_winners[1]), (court_winners[2], "Bye")]
    elif len(court_winners) == 4:
        semi_final_pairings = [(court_winners[0], court_winners[1]), (court_winners[2], court_winners[3])]
    return semi_final_pairings



def determine_final_pairing(semi_final_winners):
    """
    Determines the final match pairing based on the winners of the semi-finals.

    Args:
        semi_final_winners (list): A list of the winning teams from the semi-final matches.

    Returns:
        tuple: A tuple representing the final match pairing.
    """
    if len(semi_final_winners) == 2:
        return (semi_final_winners[0], semi_final_winners[1])
    else:
        return ()



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
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # Semi-Final Pairings
    elements.append(Paragraph("Semi-Final Pairings:", styles['Heading2']))
    if semi_final_pairings:
        data_semi = [["Match", "Team 1", "Team 2"]]
        for i, (team1, team2) in enumerate(semi_final_pairings):
            data_semi.append([f"Match {i + 1}", team1, team2])
        table_semi = Table(data_semi)
        table_semi.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#003366'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
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
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
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

    # Initialize session state variables
    if 'generate_tournament' not in st.session_state:
        st.session_state.generate_tournament = False
    if 'team_assignments' not in st.session_state:
        st.session_state.team_assignments = {}
    if 'court_winners' not in st.session_state:
        st.session_state.court_winners = {}  # Change to dict
    if 'semi_final_pairings' not in st.session_state:
        st.session_state.semi_final_pairings = []
    if 'semi_final_winners' not in st.session_state:
        st.session_state.semi_final_winners = []
    if 'final_pairing' not in st.session_state:
        st.session_state.final_pairing = ()
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
            st.session_state.court_winners = {}  # Reset court winners on new tournament
            st.session_state.semi_final_pairings = []
            st.session_state.semi_final_winners = []
            st.session_state.final_pairing = ()

    if st.session_state.generate_tournament:
        team_assignments = st.session_state.get("team_assignments", {})
        if not team_assignments:
            st.stop()
        st.success("Tournament layout generated successfully!")

        all_courts_done = True
        # Collect court winners
        for court in range(1, num_courts + 1):
            st.subheader(f"Court {court} Results")
            # Ensure that the selectbox options are only the teams playing on that court
            winner = st.selectbox(
                f"Winner of Court {court}:",
                team_assignments[court],
                index=(
                    team_assignments[court].index(st.session_state.court_winners.get(court))
                    if st.session_state.court_winners.get(court) is not None
                    else 0
                ),
                key=f"court_winner_{court}",  # Unique key for each selectbox
            )
            st.session_state.court_winners[court] = winner # changed to court
            if st.session_state.court_winners.get(court) is None: # changed to court
                all_courts_done = False
        
        if all_courts_done:
            # Determine Semi-Finals
            court_winners_list = [st.session_state.court_winners[i] for i in sorted(st.session_state.court_winners.keys())]
            st.session_state.semi_final_pairings = determine_semi_finals(court_winners_list)
            semi_final_winners = []

            # Display Semi-Finals and collect winners
            st.subheader("Semi-Final Results")
            if st.session_state.semi_final_pairings:
                for i, (team1, team2) in enumerate(st.session_state.semi_final_pairings):
                    if "Bye" not in (team1, team2):
                        winner = st.selectbox(
                            f"Winner of Semi-Final {i + 1} ({team1} vs {team2}):",
                            [team1, team2],
                            key=f"semi_final_winner_{i}",  # Unique key
                        )
                        semi_final_winners.append(winner)
                    else:
                        winner = team1 if team1 != "Bye" else team2
                        st.write(f"Winner of Semi-Final {i + 1} ({team1} vs {team2}): {winner}")
                        semi_final_winners.append(winner)
            else:
                st.write("N/A")
            st.session_state.semi_final_winners = semi_final_winners
            # Determine Finals
            st.session_state.final_pairing = determine_final_pairing(st.session_state.semi_final_winners)
            
            # Generate and Download PDF
            pdf_buffer = create_pdf_layout(
                team_assignments, st.session_state.semi_final_pairings, st.session_state.final_pairing, num_courts
            )
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

            st.subheader("Semi-Final Pairings:")
            if st.session_state.semi_final_pairings:
                for pairing in st.session_state.semi_final_pairings:
                    st.write(f"{pairing[0]} vs {pairing[1]}")
            else:
                st.write("N/A")

            st.subheader("Final Pairing:")
            if st.session_state.final_pairing:
                st.write(f"{st.session_state.final_pairing[0]} vs {st.session_state.final_pairing[1]}")
            else:
                st.write("N/A")
        else:
            st.write("Please select the winner for all courts.")
if __name__ == "__main__":
    main()
