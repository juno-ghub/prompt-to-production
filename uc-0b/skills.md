skills:
  - name: retrieve_policy
    description: Loads a policy .txt file and returns it as structured numbered sections with clause identifiers.
    input: File path (string) to a .txt policy document.
    output: Dictionary with section numbers as keys (e.g., "2.3", "3.2", "5.2") and clause text as values.
    error_handling: If file not found, raise FileNotFoundError with path. If format is invalid, log warning and return raw text.

  - name: enforce_clause_inventory
    description: Validates that a summary contains all 10 required clauses and that multi-condition clauses preserve every condition.
    input: Summary text (string) and clause inventory list (list of 10 clause identifiers).
    output: Dictionary with keys "present" (list of found clauses), "missing" (list not found), "condition_loss" (list of clauses where a sub-condition was dropped).
    error_handling: If a clause's conditions cannot be verified (e.g., ambiguous paraphrase), flag for manual review and log "UNVERIFIABLE".

  - name: summarize_policy
    description: Takes structured policy sections and generates a concise summary that includes all required clauses, binding verbs intact, no scope bleed.
    input: Dictionary of sections (from retrieve_policy) and clause inventory (10-clause list).
    output: String summary with clause references (e.g., "[2.3]") and validation report showing all 10 clauses present.
    error_handling: If a clause cannot fit without meaning loss, quote verbatim and mark "[VERBATIM]". If external context is needed, refuse and log "EXTERNAL_CONTEXT_REQUIRED".
