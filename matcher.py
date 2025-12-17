import random
import copy

def is_valid_assignment(giver, receiver):
    """
    Checks if a specific assignment is valid based on constraints.
    """
    # 1. Self-exclusion
    if giver['name'] == receiver['name']:
        return False
    
    # 2. Relationship exclusion
    # If giver has a 'relationship' field, they cannot give to that person.
    # We strip and lower to ensure robust matching.
    excluded_name = (giver.get('relationship') or "").strip().lower()
    receiver_name = (receiver.get('name') or "").strip().lower()
    
    if excluded_name and excluded_name == receiver_name:
        return False
        
    return True

def generate_assignments(participants, max_attempts=1000):
    """
    Generates a valid Secret Santa assignment list.
    Returns: List of tuples (giver_dict, receiver_dict) or None if failed.
    """
    if not participants:
        return []

    # Deep copy to avoid mutating original list during shuffling
    givers = participants
    receivers = copy.deepcopy(participants)
    
    for attempt in range(max_attempts):
        random.shuffle(receivers)
        
        assignments = []
        valid_round = True
        
        for i, giver in enumerate(givers):
            receiver = receivers[i]
            
            if not is_valid_assignment(giver, receiver):
                valid_round = False
                break
            
            assignments.append((giver, receiver))
        
        if valid_round:
            return assignments
            
    return None
