from matcher import generate_assignments

def test_matching():
    # Dummy data
    participants = [
        {'name': 'Ricardo', 'relationship': 'Liliana', 'email': 'r@test.com'},
        {'name': 'Liliana', 'relationship': 'Ricardo', 'email': 'l@test.com'},
        {'name': 'Juan', 'relationship': '', 'email': 'j@test.com'},
        {'name': 'Maria', 'relationship': '', 'email': 'm@test.com'},
        {'name': 'Pedro', 'relationship': 'Juan', 'email': 'p@test.com'}, # Pedro refuses to give to Juan
    ]

    print("--- Running Matching Test ---")
    assignments = generate_assignments(participants)
    
    if not assignments:
        print("FAILED: Could not generate assignments.")
        return

    print("Success! Assignments:")
    for giver, receiver in assignments:
        print(f"{giver['name']} ({giver['relationship']}) -> {receiver['name']}")
        
        # Verify constraints again
        if giver['name'] == receiver['name']:
            print("ERROR: Self-gift!")
        if giver['relationship'] == receiver['name']:
            print(f"ERROR: Relationship violation! {giver['name']} -> {receiver['name']}")

    # Test failure case (impossible loop)
    # e.g. A excludes B, B excludes A, only 2 people.
    print("\n--- Running Impossible Case Test ---")
    impossible_participants = [
        {'name': 'A', 'relationship': 'B'},
        {'name': 'B', 'relationship': 'A'}
    ]
    res = generate_assignments(impossible_participants, max_attempts=10)
    if res is None:
        print("Correctly failed on impossible case.")
    else:
        print("ERROR: Generated assignment for impossible case!")

if __name__ == "__main__":
    test_matching()
