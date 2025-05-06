import streamlit as st
import random
import math
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO

# --- Helper Functions ---
def get_bracket_size(num_teams):
    """Finds the smallest power of 2 >= num_teams."""
    if num_teams < 1:
        return 1
    return 2**math.ceil(math.log2(num_teams))

def get_num_rounds(bracket_size):
    """Calculates the number of rounds for a given bracket size."""
    if bracket_size < 2:
        return 0
    return int(math.log2(bracket_size))

def initialize_bracket_structure_with_courts(num_teams, num_courts):
    """Initializes the tournament bracket structure and sets up the first round."""
    bracket_size = get_bracket_size(num_teams)
    num_rounds = get_num_rounds(bracket_size)
    byes = bracket_size - num_teams

    teams = [f"Team {i+1}" for i in range(num_teams)]
    random.shuffle(teams)

    st.session_state.teams = teams
    st.session_state.bracket_size = bracket_size
    st.session_state.num_rounds = num_rounds
    st.session_state.byes = byes
    st.session_state.num_courts = num_courts # Store number of courts
    st.session_state.match_details = {} # Store details of all potential matches by match_id
    st.session_state.rounds_match_ids = [[] for _ in range(num_rounds + 1)] # Match_ids organized by round (Index 0 unused, R1 at Index 1)
    st.session_state.next_round_feed = {} # Maps next_round_match_id to [prev_match_id1, prev_match_id2]

    # Create R1 matches and bye entries
    r1_match_ids = []
    r1_items_for_display = [] # Items for the first round display (matches + byes)

    teams_copy = list(teams)
    teams_with_byes = teams_copy[:byes]
    teams_playing_r1 = teams_copy[byes:]

    # Create R1 matches from teams_playing_r1
    for i in range(0, len(teams_playing_r1), 2):
        team1 = teams_playing_r1[i]
        team2 = teams_playing_r1[i+1]
        match_id = f'R1_M{i//2}'
        st.session_state.match_details[match_id] = {'teams': [team1, team2], 'winner': None}
        r1_match_ids.append(match_id)
        r1_items_for_display.append({'type': 'match', 'match_id': match_id, 'teams': [team1, team2]})

    # Create bye entries (teams with byes automatically win their 'match')
    bye_items_for_display = []
    for i, team in enumerate(teams_with_byes):
        bye_match_id = f'R1_B{i}'
        st.session_state.match_details[bye_match_id] = {'teams': [team, 'BYE'], 'winner': team}
        r1_match_ids.append(bye_match_id)
        bye_items_for_display.append({'type': 'bye', 'match_id': bye_match_id, 'team': team})

    # Store R1 match_ids (both actual matches and bye 'matches')
    st.session_state.rounds_match_ids[1] = r1_match_ids

    # Combine and shuffle R1 display items for court assignment
    all_r1_display_items = r1_items_for_display + bye_items_for_display
    random.shuffle(all_r1_display_items)

    # Assign courts to R1 display items
    for i, item in enumerate(all_r1_display_items):
        item['court'] = (i % num_courts) + 1

    # Set the current round items for display
    st.session_state.current_round_items = all_r1_display_items
    st.session_state.current_round_index = 1 # Start with Round 1
    st.session_state.tournament_started = True
    st.session_state.tournament_finished = False
    st.session_state.final_winner = None
    st.session_state.round_winners_in_progress = {} # To store selected winners before advancing

    # Build the structure of subsequent rounds' matches (feed)
    prev_round_match_ids = r1_match_ids
    for round_index in range(2, num_rounds + 1):
        current_round_match_ids = []
        # Pair up the match_ids from the previous round's results
        for i in range(0, len(prev_round_match_ids), 2):
            if i + 1 < len(prev_round_match_ids):
                match_id = f'R{round_index}_M{i//2}'
                # Teams are unknown at this stage, will be filled when advancing
                st.session_state.match_details[match_id] = {'teams': [None, None], 'winner': None}
                # Store which previous matches feed into this one
                st.session_state.next_round_feed[match_id] = [prev_round_match_ids[i], prev_round_match_ids[i+1]]
                current_round_match_ids.append(match_id)
            # If there's an odd number of winners from the previous round, the last one
            # would get a bye in this round, but our R1 bye logic prevents this in a standard bracket.
            # This case should ideally not be reached if R1 byes are handled correctly.

        st.session_state.rounds_match_ids[round_index] = current_round_match_ids
        prev_round_match_ids = current_round_match_ids

    # Identify the final match_id
    if num_rounds >= 1 and len(st.session_state.rounds_match_ids[num_rounds]) == 1:
         st.session_state.final_match_id = st.session_state.rounds_match_ids[num_rounds][0]
    else:
         st.session_state.final_match_id = None # Should not happen for 8-16 teams


def display_current_round():
    """Displays the matches for the current round and collects winner selections."""
    st.header(f"Round {st.session_state.current_round_index}")
    st.write("Select the winner for each match.")

    current_round_winners = {}
    all_winners_selected = True

    # Iterate through the items prepared for the current round display
    for i, item in enumerate(st.session_state.current_round_items):
        item_type = item['type']
        match_id = item['match_id']
        teams = item['teams']
        court_info = f" (Court {item['court']})" if 'court' in item else ""

        if item_type == 'bye':
            team = teams[0]
            st.write(f"Match {i+1}{court_info}: **{team}** gets a BYE")
            current_round_winners[match_id] = team # Winner is the team with bye
        elif item_type == 'match':
            team1, team2 = teams
            st.write(f"Match {i+1}{court_info}: **{team1}** vs **{team2}**")

            # Get pre-selected winner if available (e.g., after rerun)
            selected_winner = st.session_state.get('round_winners_in_progress', {}).get(match_id)

            # Ensure teams are not None before creating radio buttons
            if team1 is not None and team2 is not None:
                 winner_selection = st.radio(
                     f"Winner for Match {i+1}:",
                     [team1, team2],
                     key=f"winner_{match_id}", # Use match_id for unique key
                     index=[team1, team2].index(selected_winner) if selected_winner in [team1, team2] else None
                 )

                 if winner_selection:
                     current_round_winners[match_id] = winner_selection
                     # Store selected winner in session state immediately
                     if 'round_winners_in_progress' not in st.session_state:
                         st.session_state.round_winners_in_progress = {}
                     st.session_state.round_winners_in_progress[match_id] = winner_selection
                 else:
                     all_winners_selected = False
            else:
                 st.warning(f"Match {i+1} is missing teams.")
                 all_winners_selected = False # Cannot advance if teams are missing

    return current_round_winners, all_winners_selected

def advance_to_next_round_structured(current_round_winners):
    """Processes the current round's winners and sets up the next round."""
    # Update winners in the main match_details dictionary
    for match_id, winner in current_round_winners.items():
        if match_id in st.session_state.match_details:
            st.session_state.match_details[match_id]['winner'] = winner

    # Clear winners in progress for the next round
    st.session_state.round_winners_in_progress = {}

    # Move to the next round index
    st.session_state.current_round_index += 1

    next_round_index = st.session_state.current_round_index

    # Check if the tournament is finished
    if next_round_index > st.session_state.num_rounds:
        st.session_state.tournament_finished = True
        if st.session_state.final_match_id and st.session_state.final_match_id in st.session_state.match_details:
             st.session_state.final_winner = st.session_state.match_details[st.session_state.final_match_id]['winner']
        else:
             st.session_state.final_winner = "Undetermined" # Should not happen for a full bracket
        st.balloons() # Celebrate the winner!
        return

    # Get the match_ids for the next round
    next_round_match_ids = st.session_state.rounds_match_ids[next_round_index]
    next_round_items_for_display = []

    # Set up the matches for the next round based on winners from the previous round
    for match_id in next_round_match_ids:
        # Find the match_ids from the previous round that feed into this match
        # Add check if match_id exists in next_round_feed
        if match_id in st.session_state.next_round_feed:
            feed1_id, feed2_id = st.session_state.next_round_feed[match_id]

            # Get the winners from the previous round's matches
            # Add checks if feed_ids exist in match_details and have winners
            team1 = st.session_state.match_details.get(feed1_id, {}).get('winner')
            team2 = st.session_state.match_details.get(feed2_id, {}).get('winner')

            # Update the teams for this match in match_details
            st.session_state.match_details[match_id]['teams'] = [team1, team2]

            # Add this match to the list of items to display for the next round
            next_round_items_for_display.append({
                'type': 'match',
                'match_id': match_id,
                'teams': [team1, team2],
                'winner': None # Winner not selected yet for this round
            })
        else:
            st.error(f"Error setting up match {match_id}: Feed information missing.")


    # Update the current round items for display
    st.session_state.current_round_items = next_round_items_for_display
    st.session_state.tournament_finished = False # Tournament is not finished yet

def create_tournament_pdf_structured():
    """Generates a PDF summary of the tournament results."""
    # Add checks for required session state keys before proceeding
    required_keys = ['teams', 'num_rounds', 'rounds_match_ids', 'match_details', 'tournament_finished', 'final_winner']
    if not all(key in st.session_state for key in required_keys):
        st.error("Tournament data is incomplete or missing. Cannot generate PDF.")
        return None # Return None if data is missing

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Tennis Tournament Results", styles['h1']))
    elements.append(Spacer(1, 0.2 * inch))

    # Initial Teams
    elements.append(Paragraph("Initial Teams:", styles['h2']))
    initial_teams_text = ", ".join(st.session_state.teams)
    elements.append(Paragraph(initial_teams_text, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    # Display results of each round
    # Check if num_rounds is a valid number before iterating
    if isinstance(st.session_state.num_rounds, int) and st.session_state.num_rounds >= 1:
        for r_index in range(1, st.session_state.num_rounds + 1):
             elements.append(Paragraph(f"Round {r_index} Results:", styles['h2']))
             # Check if round_match_ids exists for this round index
             round_match_ids = st.session_state.rounds_match_ids[r_index] if r_index < len(st.session_state.rounds_match_ids) else []

             if not round_match_ids: # Skip if no matches in this round
                  elements.append(Paragraph("No matches in this round.", styles['Normal']))
                  continue

             for match_id in round_match_ids:
                 match_details = st.session_state.match_details.get(match_id)
                 if match_details:
                     team1, team2 = match_details.get('teams', [None, None])
                     winner = match_details.get('winner')
                     if team2 == 'BYE':
                         elements.append(Paragraph(f"{team1} gets a BYE", styles['Normal']))
                     else:
                         result_text = f"{team1} vs {team2}"
                         if winner:
                             result_text += f" - Winner: {winner}"
                         elements.append(Paragraph(result_text, styles['Normal']))
                 else:
                      elements.append(Paragraph(f"Details missing for match {match_id}.", styles['Normal']))
             elements.append(Spacer(1, 0.2 * inch))
    else:
        elements.append(Paragraph("Tournament rounds data is incomplete.", styles['Normal']))


    # Display Final Winner
    if st.session_state.tournament_finished and st.session_state.final_winner:
         elements.append(Paragraph("Tournament Champion:", styles['h2']))
         elements.append(Paragraph(st.session_state.final_winner, styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# --- Streamlit App Layout ---
st.title("Tennis Tournament Simulator")

# Initialize session state using a single flag
if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    # Initialize all other necessary keys with default values
    st.session_state.tournament_started = False
    st.session_state.tournament_finished = False
    st.session_state.final_winner = None
    st.session_state.round_winners_in_progress = {}
    st.session_state.teams = []
    st.session_state.bracket_size = 0
    st.session_state.num_rounds = 0
    st.session_state.byes = 0
    st.session_state.num_courts = 0
    st.session_state.match_details = {}
    st.session_state.rounds_match_ids = []
    st.session_state.next_round_feed = {}
    st.session_state.current_round_items = []
    st.session_state.current_round_index = 0
    st.session_state.final_match_id = None


# Input section (only shown before the tournament starts)
if not st.session_state.tournament_started:
    st.sidebar.header("Tournament Setup")
    num_teams = st.sidebar.number_input("Number of teams (8-16):", min_value=8, max_value=16, value=8, step=1)
    num_courts = st.sidebar.number_input("Number of courts (2-4):", min_value=2, max_value=4, value=2, step=1)

    if st.sidebar.button("Start Tournament"):
        initialize_bracket_structure_with_courts(num_teams, num_courts)
        st.rerun() # Rerun to show the first round
else:
    # Display current setup when tournament has started
    st.sidebar.header("Current Tournament Setup")
    st.sidebar.write(f"Teams: {len(st.session_state.teams)}")
    st.sidebar.write(f"Courts: {st.session_state.num_courts}")
    st.sidebar.write(f"Current Round: {st.session_state.current_round_index}")


# Tournament in progress
if st.session_state.tournament_started and not st.session_state.tournament_finished:
    current_round_winners, all_winners_selected = display_current_round()

    # Check if all matches in the current round have winners selected
    # We can infer this by comparing the number of selected winners to the number of items
    # in the current round display list that are actual matches (not byes).
    num_actual_matches_in_round = sum(1 for item in st.session_state.current_round_items if item['type'] == 'match')

    if all_winners_selected and num_actual_matches_in_round > 0: # Only show button if there are matches and all winners are selected
        if st.button("Advance to Next Round"):
            # Pass the collected winners to the advance function
            advance_to_next_round_structured(current_round_winners)
            st.rerun() # Rerun to show the next round or final result
    elif num_actual_matches_in_round > 0 and not all_winners_selected:
        st.info("Please select winners for all matches to advance.")


# Tournament finished
elif st.session_state.tournament_finished:
    st.header("Tournament Complete!")
    # Add check before displaying final winner
    if st.session_state.final_winner:
        st.subheader(f"Champion: {st.session_state.final_winner}")
    else:
        st.subheader("Tournament finished, but champion could not be determined.")


    # --- PDF Generation Button ---
    st.write("---")
    st.subheader("Download Tournament Results")
    pdf_buffer = create_tournament_pdf_structured()
    # Only show the download button if PDF buffer was successfully created
    if pdf_buffer:
        st.download_button(
            label="Download PDF Results",
            data=pdf_buffer,
            file_name="tournament_results.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Could not generate PDF due to missing tournament data.")


# --- Reset Button ---
if st.session_state.tournament_started or st.session_state.tournament_finished:
    st.sidebar.write("---")
    if st.sidebar.button("Reset Tournament"):
        # Clear all session state variables to reset the app
        for key in list(st.session_state.keys()): # Use list() to avoid RuntimeError during iteration
            del st.session_state[key]
        st.rerun() # Rerun to go back to the setup screen

