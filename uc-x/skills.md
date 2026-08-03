skills:
  - name: retrieve_documents
    description: Loads all three policy documents and indexes them by document name and section number for searchable lookup.
    input: Directory path containing policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt (default: ../data/policy-documents/).
    output: Dictionary indexed as {document_name: {section_number: section_text}}. Example: {"policy_hr_leave.txt": {"2.6": "text...", "5.2": "text..."}}
    error_handling: If file not found, raise FileNotFoundError. If parsing fails, log warning and return empty section. If all files missing, exit with error "Cannot load policy documents".

  - name: search_single_document
    description: Searches a single policy document for answer to a question using section content matching, returns section and text or None.
    input: Question (string), document_name (string), indexed_documents (dict from retrieve_documents).
    output: Dictionary {found: bool, section_id: str, text: str, document: str} if answer found. {found: false} if not found.
    error_handling: If question is ambiguous, search multiple sections and return all matches. If document not in index, return {found: false, error: "document not indexed"}.

  - name: answer_question
    description: Answers a user question by searching all three documents, enforcing single-source rule, and returning answer with citation OR refusal template.
    input: Question (string), indexed_documents (dict).
    output: String containing either (1) single-source answer with [document_name, section X.Y] citation, OR (2) refusal template exactly as specified.
    error_handling: If answer found in multiple documents, refuse using template (possible cross-document blend). If no document contains answer, refuse using template. Never return partial answers or hedged responses.
