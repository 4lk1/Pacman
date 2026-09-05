# Team Organization

## Roles

This activity was carried out by aleka and gkordhak; the split below documents how responsibilities were handled:

| Role                | Team Member(s)   | Responsibility                                                              |
|---------------------|------------------|-----------------------------------------------------------------------------|
| Requirements owner  | aleka, gkordhak  | Read the subject, built the requirement checklist, final compliance audit.   |
| Architect           | aleka, gkordhak  | Module split (config/maze/highscore/game/ai/render/ui/app), movement model. |
| Developer           | aleka, gkordhak  | Implemented all modules and the entry point.                                |
| Tester              | aleka, gkordhak  | Wrote and ran the pytest suite, flake8 and mypy, headless smoke runs.       |
| Documenter          | aleka, gkordhak  | README, project management documents, packaging and deployment docs.        |
| Reviewer            | aleka, gkordhak  | Walked through the PDF again at the end, verified every requirement.        |

## How decisions were made

- Every decision was recorded in [`analysis.md`](analysis.md) with its
  rationale, and mapped back to a requirement from the subject.
- Ambiguities were resolved by re-reading the subject first, then by
  choosing the interpretation that follows the explicit text most
  directly (examples: `pacgum` interpreted as a percentage; timeout
  behavior chosen from the options the subject lists).
- Code review was done in two passes: first against the requirement
  checklist, then against the test results and lint output.

## How issues were handled

- Each issue found during testing was logged, fixed and re-verified
  (see [`acceptance_test_plan.md`](acceptance_test_plan.md) for the
  list of bugs found and fixed).
- No unresolved issues remain at the end of the activity.