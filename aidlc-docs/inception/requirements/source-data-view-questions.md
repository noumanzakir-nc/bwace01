# Source Data View — Clarifying Questions

Please answer each question by filling in the letter choice after the `[Answer]:` tag. If none of the options match your needs, choose the last option (Other) and describe your preference.

## Question 1
Which datasets should the new view expose?

A) All six raw source datasets (Object Inventory, Usage Logs, Criticality Matrix, Dependency Map, Data Volume, Complexity Scores), whether bundled or uploaded

B) Only the currently active dataset (bundled or uploaded), same six tables

C) Only the Object Inventory table (the primary object list), not the other five

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
Where should this new capability live in the app?

A) A new sidebar navigation entry, "Source Data", alongside the existing five views (Dashboard, Object Detail, Dependencies, Wave Planner, Scenario Compare)

B) An expander/section added to the existing sidebar "Data Sources" area (where uploads already happen), not a separate view

C) A tab or expander added inside the existing Dashboard view

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
What format should each dataset be shown in?

A) A plain read-only table per dataset (one table each, selectable via a dropdown or tabs), showing every column and row exactly as loaded

B) A single combined table joining all six datasets by object ID

C) A summary/preview only (e.g. first N rows) rather than the full dataset

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
Should the view support search/filter within a dataset table?

A) No — a plain static table is sufficient for this PoC

B) Yes — a simple text search box that filters rows by any column

C) Yes — column-level filters (e.g. dropdowns per column)

D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
Should users be able to export/download the raw data from this view?

A) No — viewing only; export already exists elsewhere (classification CSV, wave plan JSON) and is out of scope here

B) Yes — add a per-dataset "Download as CSV" button

C) Yes — add a single "Download all as ZIP" button

D) Other (please describe after [Answer]: tag below)

[Answer]: B
