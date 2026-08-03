"""
UC-X app.py — Interactive Policy Question Answering System
Answers employee questions from three policy documents using single-source enforcement.
Prevents cross-document blending, hedging, and hallucination.
Run: python app.py
"""
import os
import sys
import re
from pathlib import Path

# Refusal template (exactly as specified in README.md)
REFUSAL_TEMPLATE = """This question is not covered in the available policy documents (policy_hr_leave.txt, policy_it_acceptable_use.txt, policy_finance_reimbursement.txt). Please contact the relevant team for guidance."""

# Policy document paths
POLICY_DIR = Path(__file__).parent.parent / "data" / "policy-documents"
POLICIES = {
    "policy_hr_leave.txt": POLICY_DIR / "policy_hr_leave.txt",
    "policy_it_acceptable_use.txt": POLICY_DIR / "policy_it_acceptable_use.txt",
    "policy_finance_reimbursement.txt": POLICY_DIR / "policy_finance_reimbursement.txt",
}

def load_documents():
    """Load and index all policy documents by section number."""
    documents = {}
    
    for doc_name, doc_path in POLICIES.items():
        if not doc_path.exists():
            print(f"ERROR: {doc_name} not found at {doc_path}")
            sys.exit(1)
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse sections by section number pattern (e.g., "2.3", "5.2")
        sections = {}
        section_pattern = r'^(\d+\.\d+)\s+(.+?)(?=^\d+\.\d+\s+|^=|$)'
        
        for match in re.finditer(section_pattern, content, re.MULTILINE | re.DOTALL):
            section_id = match.group(1)
            section_text = match.group(2).strip()
            sections[section_id] = section_text
        
        documents[doc_name] = sections
        print(f"✓ Loaded {doc_name}: {len(sections)} sections")
    
    return documents

def search_documents(question, documents):
    """Search all documents for relevant sections. Return findings."""
    findings = {}
    
    # Normalize question for matching
    q_lower = question.lower()
    
    for doc_name, sections in documents.items():
        matches = []
        for section_id, section_text in sections.items():
            text_lower = section_text.lower()
            
            # Simple keyword matching
            if any(word in text_lower for word in q_lower.split()):
                # Score by how many keywords match
                keyword_count = sum(1 for word in q_lower.split() if word in text_lower)
                matches.append({
                    "section_id": section_id,
                    "text": section_text,
                    "score": keyword_count
                })
        
        if matches:
            # Sort by relevance score
            matches.sort(key=lambda x: x['score'], reverse=True)
            findings[doc_name] = matches
    
    return findings

def answer_question(question, documents):
    """Answer question from single document, or return refusal."""
    print(f"\n> {question}\n")
    
    findings = search_documents(question, documents)
    
    # No findings in any document
    if not findings:
        print(REFUSAL_TEMPLATE)
        return
    
    # Multiple documents have relevant sections — potential blend risk
    if len(findings) > 1:
        # Exception: Some questions legitimately need multi-doc context check
        # but we should still refuse if answer isn't clear from single source
        print(REFUSAL_TEMPLATE)
        return
    
    # Single document found — answer from it
    doc_name = list(findings.keys())[0]
    matches = findings[doc_name]
    
    if matches:
        # Return the highest-scoring match
        top_match = matches[0]
        section_id = top_match['section_id']
        section_text = top_match['text']
        
        # Format answer with citation
        answer = f"{section_text}\n\n[Source: {doc_name}, section {section_id}]"
        print(answer)
    else:
        print(REFUSAL_TEMPLATE)

def validate_no_hedging(response):
    """Check for hedging phrases that indicate hallucination."""
    hedging_phrases = [
        "while not explicitly covered",
        "typically",
        "generally understood",
        "it is common practice",
        "usually",
        "likely",
        "generally",
        "tends to",
        "appears to"
    ]
    
    response_lower = response.lower()
    for phrase in hedging_phrases:
        if phrase in response_lower:
            return False  # Found hedging
    return True

def main():
    print("="*80)
    print("POLICY QUESTION ANSWERING SYSTEM")
    print("CMC Employee Policy Assistant")
    print("="*80)
    print("\nLoading policy documents...\n")
    
    try:
        documents = load_documents()
    except Exception as e:
        print(f"ERROR: Failed to load documents: {e}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("Ready. Type your question (or 'exit' to quit):")
    print("="*80)
    
    while True:
        try:
            question = input("\nYour question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'bye']:
                print("\nThank you. Goodbye.")
                break
            
            answer_question(question, documents)
            
        except KeyboardInterrupt:
            print("\n\nExiting. Goodbye.")
            break
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    main()
