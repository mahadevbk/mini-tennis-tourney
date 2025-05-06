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
    """Creates the initial tournament structure and assigns courts for Round 1."""
    bracket_size = get_bracket_size(num_teams)
    num_rounds = get_num_rounds(bracket_size)
    byes = bracket_size - num_teams

    teams = [f"Team {i+1}" for i in range(num_teams)]
    random.shuffle(teams)

    st.session_state.teams = teams
    st.session_state.bracket_size = bracket_size
    st.session_state.num_rounds = num_rounds
    st.session_state.byes = byes
    st.session_state.num_courts = num_courts
    st.session_state.match_details = {}
    st.session_state.rounds_match_ids = [[] for _ in range(num_rounds + 1)]
    st.session_state.next_round_feed = {}

    # Create R1 matches and bye entries
    r1_match_ids = []
    r1_items_for_display = []

    teams_copy = list(teams)
    teams_with_byes = teams_copy[:byes]
    teams_playing_r1 = teams_copy[byes:]

    for i in range(0, len(teams_playing_r1), 2):
        team1 = teams_playing_r1[i]
        team2 = teams_playing_r1[i+1]
        match_id = f'R1_M{i//2}'
        st.session_state.match_details[match_id] = {'teams': [team1, team2], 'winner': None}
        r1_match_ids.append(match_id)
        r1_items_for_display.append({'type': 'match', 'match_id': match_id, 'teams': [team1, team2]})

    bye_items_for_display = []
    for i, team in enumerate(teams_with_byes):
        bye_match_id = f'R1_B{i}'
        # Note: Bye items use 'team' (singular) key in the display item structure
        st.session_state.match_details[bye_match_id] = {'teams': [team, 'BYE'], 'winner': team} # Still store as ['Team', 'BYE'] in match_details for consistency
        r1_match_ids.append(bye_match_id)
        bye_items_for_display.append({'type': 'bye', 'match_id': bye_match_id, 'team': team}) # Store as 'team' in display items

    st.session_state.rounds_match_ids[1] = r1_match_ids

    all_r1_display_items = r1_items_for_display + bye_items_for_display
    random.shuffle(all_r1_display_items)

    # Assign courts to R1 display items
    for i, item in enumerate(all_r1_display_items):
        item['court'] = (i % num_courts) + 1

    st.session_state.current_round_items = all_r1_display_items
    st.session_state.current_round_index = 1
    st.session_state.tournament_started = True
    st.session_state.tournament_finished = False
    st.session_state.final_winner = None
    st.session_state.round_winners_in_progress = {}

    prev_round_match_ids = r1_match_ids
    for round_index in range(2, num_rounds + 1):
        current_round_match_ids = []
        for i in range(0, len(prev_round_match_ids), 2):
            if i + 1 < len(prev_round_match_ids):
                match_id = f'R{round_index}_M{i//2}'
                st.session_state.match_details[match_id] = {'teams': [None, None], 'winner': None}
                st.session_state.next_round_feed[match_id] = [prev_round_match_ids[i], prev_round_match_ids[i+1]]
                current_round_match_ids.append(match_id)

        st.session_state.rounds_match_ids[round_index] = current_round_match_ids
        prev_round_match_ids = current_round_match_ids

    # Identify the final match_id
    if num_rounds >= 1 and len(st.session_state.rounds_match_ids[num_rounds]) == 1:
         st.session_state.final_match_id = st.session_state.rounds_match_ids[num_rounds][0]
    else:
         st.session_state.final_match_id = None


def display_current_round():
    """Displays the matches for the current round and collects winner selections."""
    st.header(f"Round {st.session_state.current_round_index}")
    st.write("Select the winner for each match.")

    current_round_winners = {}
    all_winners_selected = True

    # Iterate through the items prepared for the current round display
    for i, item in enumerate(st.session_state.current_round_items):
        # Use .get() with default values for robustness
        item_type = item.get('type')
        match_id = item.get('match_id')
        court = item.get('court') # Use .get() here

        # Basic check for essential keys
        if item_type is None or match_id is None:
             st.warning(f"Skipping invalid item {i+1} due to missing type or match_id: {item}")
             all_winners_selected = False # Cannot advance if data is missing
             continue # Skip to the next item

        # Display court assignment explicitly and prominently
        if court is not None:
            st.subheader(f"**Court {court}**") # Using subheader to make it stand out
            st.write(f"Match {i+1}:") # Display match number after court


        if item_type == 'bye':
            team = item.get('team') # Get team name using 'team' key for bye items
            if team:
                 st.write(f"**{team}** gets a BYE")
                 current_round_winners[match_id] = team
            else:
                 st.warning(f"Skipping bye item {i+1} due to missing team name: {item}")
                 all_winners_selected = False

        elif item_type == 'match':
            teams = item.get('teams') # Get teams list using 'teams' key for match items
            if teams is not None and isinstance(teams, list) and len(teams) >= 2:
                team1 = teams[0]
                team2 = teams[1]

                st.write(f"**{team1}** vs **{team2}**") # Display teams after court and match number

                selected_winner = st.session_state.get('round_winners_in_progress', {}).get(match_id)

                winner_selection = st.radio(
                    f"Winner for Match {i+1} on Court {court}:", # Include court in radio button label for clarity
                    [team1, team2],
                    key=f"winner_{match_id}",
                    index=[team1, team2].index(selected_winner) if selected_winner in [team1, team2] else None
                )

                if winner_selection:
                    current_round_winners[match_id] = winner_selection
                    if 'round_winners_in_progress' not in st.session_state:
                        st.session_state.round_winners_in_progress = {}
                    st.session_state.round_winners_in_progress[match_id] = winner_selection
                else:
                    all_winners_selected = False
            else:
                 st.warning(f"Match {i+1} is missing required teams or teams data is invalid: {item}")
                 all_winners_selected = False # Cannot advance if teams are missing
        else:
            st.warning(f"Skipping item {i+1} with unknown type '{item_type}': {item}")
            all_winners_selected = False

        st.write("---") # Add a separator for clarity between matches


    return current_round_winners, all_winners_selected

def advance_to_next_round_structured(current_round_winners):
    """Processes the current round's winners and sets up the next round."""
    for match_id, winner in current_round_winners.items():
        if match_id in st.session_state.match_details:
            st.session_state.match_details[match_id]['winner'] = winner

    st.session_state.round_winners_in_progress = {}
    st.session_state.current_round_index += 1
    next_round_index = st.session_state.current_round_index

    if next_round_index > st.session_state.num_rounds:
        st.session_state.tournament_finished = True
        if st.session_state.final_match_id and st.session_state.final_match_id in st.session_state.match_details:
             st.session_state.final_winner = st.session_state.match_details[st.session_state.final_match_id]['winner']
        else:
             st.session_state.final_winner = "Undetermined"
        st.balloons()
        return

    next_round_match_ids = st.session_state.rounds_match_ids[next_round_index]
    next_round_items_for_display = []

    for match_id in next_round_match_ids:
        if match_id in st.session_state.next_round_feed:
            feed1_id, feed2_id = st.session_state.next_round_feed[match_id]

            team1 = st.session_state.match_details.get(feed1_id, {}).get('winner')
            team2 = st.session_state.match_details.get(feed2_id, {}).get('winner')

            st.session_state.match_details[match_id]['teams'] = [team1, team2]

            # Create the display item for the next round match
            next_round_items_for_display.append({
                'type': 'match',
                'match_id': match_id,
                'teams': [team1, team2],
                'winner': None
            })
        else:
            st.error(f"Error setting up match {match_id}: Feed information missing.")

    # Assign courts to the matches in the next round items for display
    # Only assign courts if there are items to display and num_courts is valid
    if next_round_items_for_display and st.session_state.num_courts > 0:
        for i, item in enumerate(next_round_items_for_display):
            item['court'] = (i % st.session_state.num_courts) + 1


    st.session_state.current_round_items = next_round_items_for_display
    st.session_state.tournament_finished = False

def create_tournament_pdf_structured():
    """Generates a PDF summary of the tournament results."""
    required_keys = ['teams', 'num_rounds', 'rounds_match_ids', 'match_details', 'tournament_finished', 'final_winner']
    if not all(key in st.session_state for key in required_keys):
        st.error("Tournament data is incomplete or missing. Cannot generate PDF.")
        return None

    if not isinstance(st.session_state.rounds_match_ids, list):
        st.error("Tournament rounds data is corrupted. Cannot generate PDF.")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Tennis Tournament Results", styles['h1']))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("Initial Teams:", styles['h2']))
    initial_teams_text = ", ".join(st.session_state.teams)
    elements.append(Paragraph(initial_teams_text, styles['Normal']))
    elements.append(Spacer(1, 0.2 * inch))

    if isinstance(st.session_state.num_rounds, int) and st.session_state.num_rounds >= 1:
        for r_index in range(1, st.session_state.num_rounds + 1):
             elements.append(Paragraph(f"Round {r_index} Results:", styles['h2']))

             if r_index >= len(st.session_state.rounds_match_ids) or not isinstance(st.session_state.rounds_match_ids[r_index], list):
                 st.warning(f"Data for Round {r_index} is missing or corrupted.")
                 elements.append(Paragraph(f"Data for Round {r_index} is missing or corrupted.", styles['Normal']))
                 continue

             round_match_ids = st.session_state.rounds_match_ids[r_index]

             if not round_match_ids:
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
        st.rerun()
else:
    # Display current setup when tournament has started
    st.sidebar.header("Current Tournament Setup")
    st.sidebar.write(f"Teams: {len(st.session_state.teams)}")
    st.sidebar.write(f"Courts: {st.session_state.num_courts}")
    st.sidebar.write(f"Current Round: {st.session_state.current_round_index}")


# Tournament in progress
if st.session_state.tournament_started and not st.session_state.tournament_finished:
    current_round_winners, all_winners_selected = display_current_round()

    # Recalculate num_actual_matches_in_round based on the items successfully processed
    num_actual_matches_in_round = sum(1 for item in st.session_state.current_round_items if item.get('type') == 'match' and item.get('teams') is not None and isinstance(item.get('teams'), list) and len(item.get('teams')) >= 2)


    if all_winners_selected and num_actual_matches_in_round > 0:
        if st.button("Advance to Next Round"):
            advance_to_next_round_structured(current_round_winners)
            st.rerun()
    elif num_actual_matches_in_round > 0 and not all_winners_selected:
        st.info("Please select winners for all matches to advance.")


# Tournament finished
elif st.session_state.tournament_finished:
    st.header("Tournament Complete!")
    if st.session_state.final_winner:
        st.subheader(f"Champion: {st.session_state.final_winner}")
    else:
        st.subheader("Tournament finished, but champion could not be determined.")

    st.write("---")
    st.subheader("Download Tournament Results")
    pdf_buffer = create_tournament_pdf_structured()
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
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

