## REQ_001 [Front] Event calendar display
- The user opens the calendar section and sees a list or grid of events.
- Each event shows its main attributes: name, date, status.
- The interface behaves correctly when there are no events.

## REQ_002 [Front] Creating and editing an event
- The user can create an event by filling in the required fields.
- Saving triggers validation of the required fields.
- The user can edit an existing event.

## REQ_003 [Back] Event status management
- An event moves through a lifecycle of statuses, for example draft, scheduled, completed.
- Transitions between statuses are validated against the system rules.
- An invalid transition is blocked and reported with an error message.

## REQ_004 [Front] Filtering and searching events
- The user can filter events by period and by status.
- The user can search for an event by name.
- Combined filters return only the matching results.

## REQ_005 [Back] Input validation and error handling
- The system rejects malformed data: dates, field lengths, special characters.
- A validation error produces a message the user can act on.
- A failed operation leaves the stored data intact.
