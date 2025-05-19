#!/usr/bin/env python3
"""
Examine weigh events to understand the structure
"""
import pandas as pd

# Load the weigh events data
df = pd.read_csv('weigh_event.csv')
print(f"Total rows: {len(df)}")
print(f"Total distinct sessions: {df['session_id'].nunique()}")

# Count of rows per session
session_counts = df['session_id'].value_counts()
print(f"\nDistribution of records per session:")
print(session_counts.value_counts().sort_index())

# Find sessions with two records (entry/exit pairs)
sessions_with_two = session_counts[session_counts == 2].index.tolist()
print(f"\nFound {len(sessions_with_two)} sessions with 2 records")

# Show a few examples
print(f"\nExample session pairs:")
for i, sid in enumerate(sessions_with_two[:3]):
    print(f"\nSession {i+1}:")
    session_data = df[df['session_id'] == sid]
    print(session_data.to_string(index=False))
    
    # Check if this is ARRIVAL->DEPARTURE sequence
    event_types = session_data['event_type'].tolist()
    has_arrival = 'ARRIVAL' in event_types
    has_departure = 'DEPARTURE' in event_types
    print(f"Has ARRIVAL and DEPARTURE: {has_arrival and has_departure}")
    
# Count sessions with both ARRIVAL and DEPARTURE
valid_pairs = 0
for sid in sessions_with_two:
    session_data = df[df['session_id'] == sid]
    event_types = set(session_data['event_type'].tolist())
    if 'ARRIVAL' in event_types and 'DEPARTURE' in event_types:
        valid_pairs += 1

print(f"\nSessions with both ARRIVAL and DEPARTURE: {valid_pairs} of {len(sessions_with_two)}")