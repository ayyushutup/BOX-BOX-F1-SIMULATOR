import fastf1
print("2026 Schedule:")
try:
    print(fastf1.get_event_schedule(2026)[['EventName', 'EventFormat']])
except Exception as e:
    print(e)
print("2025 Schedule:")
try:
    print(fastf1.get_event_schedule(2025)[['EventName', 'EventFormat']])
except Exception as e:
    print(e)
