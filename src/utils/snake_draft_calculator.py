def calculate_snake_draft_picks(draft_slot, total_teams, rounds=15):
    picks = []
    
    for round_num in range(1, rounds + 1):
        if round_num % 2 == 1: 
            pick_number = (round_num - 1) * total_teams + draft_slot + 1
        else: 
            pick_number = round_num * total_teams - draft_slot
        
        picks.append(pick_number)
    
    return picks

def get_current_round_and_pick(current_pick_number, draft_slot, total_teams):
    round_number = (current_pick_number - 1) // total_teams + 1
    
    if round_number % 2 == 1:  
        your_pick_in_round = draft_slot + 1
    else:  
        your_pick_in_round = total_teams - draft_slot
    
    return round_number, your_pick_in_round

def get_next_pick_number(draft_slot, total_teams, current_round):
    next_round = current_round + 1
    
    if next_round % 2 == 1:  
        pick_number = (next_round - 1) * total_teams + draft_slot + 1
    else:  
        pick_number = next_round * total_teams - draft_slot
    
    return pick_number

def test_snake_draft():
    
    draft_slot = 3
    total_teams = 12
    
    print(f"Draft slot: {draft_slot + 1} (0-based: {draft_slot})")
    print(f"Total teams: {total_teams}")
    print()
    
    picks = calculate_snake_draft_picks(draft_slot, total_teams, 15)
    
    print("Your pick numbers for each round:")
    for round_num, pick_num in enumerate(picks, 1):
        print(f"Round {round_num:2d}: Pick #{pick_num:3d}")
    
    print()
    print("Testing current pick detection:")
    
    test_picks = [13, 21, 28, 45, 52, 69]
    
    for pick_num in test_picks:
        round_num, pick_in_round = get_current_round_and_pick(pick_num, draft_slot, total_teams)
        next_pick = get_next_pick_number(draft_slot, total_teams, round_num)
        
        print(f"Pick #{pick_num:2d}: Round {round_num}, Pick {pick_in_round} in round, Next pick: #{next_pick}")

if __name__ == "__main__":
    test_snake_draft()
