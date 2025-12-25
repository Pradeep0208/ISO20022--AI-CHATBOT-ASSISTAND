# app/rag_engine.py
import os
import re
from typing import List, Tuple, Optional, Dict
from pypdf import PdfReader

# =====================================================
# Small Talk / Greeting Detection (NON-ISO QUERIES)
# =====================================================
GREETINGS = [
    "hi", "hello", "hey",
    "good morning", "good afternoon", "good evening",
    "how are you", "how r u",
    "thanks", "thank you"
]

def is_small_talk(query: str) -> bool:
    q = (query or "").lower().strip()
    return any(q == g or q.startswith(g) for g in GREETINGS)

# =====================================================
# Message Definitions
# =====================================================
MESSAGE_DEFINITIONS: Dict[str, str] = {
    "pain.001": "CustomerCreditTransferInitiation – customer-to-bank credit transfer initiation.",
    "pain.002": "CustomerPaymentStatusReport – status on previously sent customer payments.",
    "pain.007": "CustomerPaymentReversal – reversal of a previously executed customer payment.",
    "pain.008": "CustomerDirectDebitInitiation – direct debit initiation from customer to bank.",
    
    "pacs.002": "FIToFIPaymentStatusReport – interbank payment status.",
    "pacs.003": "FIToFICustomerDirectDebit – interbank customer direct debit.",
    "pacs.004": "PaymentReturn – return of an unaccepted or rejected payment.",
    "pacs.007": "FIToFIPaymentReversal – reversal of interbank payments.",
    "pacs.008": "FIToFICustomerCreditTransfer – interbank customer credit transfer.",
    "pacs.009": "FinancialInstitutionCreditTransfer – FI to FI credit transfer.",
    "pacs.010": "FinancialInstitutionDirectDebit – FI to FI direct debit.",
    "pacs.028": "FIToFIPaymentStatusRequest – status inquiry for an interbank payment.",
    
    "camt.026": "UnableToApply – payment cannot be applied and requires investigation.",
    "camt.027": "ClaimNonReceipt – used to claim non-receipt of a payment.",
    "camt.028": "AdditionalPaymentInformation – additional information about a payment.",
    "camt.029": "ResolutionOfInvestigation – outcome of an investigation case.",
    "camt.030": "NotificationOfCaseAssignment – notification of a new/changed case assignment.",
    "camt.031": "RejectInvestigation – rejection of an investigation.",
    "camt.032": "CancelCaseAssignment – cancellation of case assignment.",
    "camt.033": "RequestForDuplicate – request for duplicate information.",
    "camt.034": "Duplicate – duplicate information message.",
    "camt.035": "ProprietaryFormatInvestigation – investigation message in proprietary format.",
    "camt.036": "DebitAuthorisationResponse – response to debit authorisation request.",
    "camt.037": "DebitAuthorisationRequest – request for debit authorisation.",
    "camt.038": "CaseStatusReportRequest – request for case status report.",
    "camt.039": "CaseStatusReport – case status information.",
    "camt.055": "CustomerPaymentCancellationRequest – cancellation request from customer.",
    "camt.056": "FIToFIPaymentCancellationRequest – interbank payment cancellation request.",
    "camt.087": "RequestToModifyPayment – request to modify a payment.",
}
MESSAGE_CODES = set(MESSAGE_DEFINITIONS.keys())
MESSAGE_FILE_MAP: Dict[str, str] = {
    "pain": "pain_messages.pdf",
    "pacs": "pacs_messages.pdf",
    "camt": "camt_messages.pdf",
}
# =====================================================
# TOC Data
# =====================================================
SECTION_START_PAGES: Dict[str, Dict[str, int]] = {
    "pacs.002": {"functionality": 6, "structure": 7, "constraints": 11, "blocks": 15},
    "pacs.003": {"functionality": 79, "structure": 80, "constraints": 83, "blocks": 87},
    "pacs.004": {"functionality": 145, "structure": 146, "constraints": 157, "blocks": 164},
    "pacs.007": {"functionality": 353, "structure": 354, "constraints": 359, "blocks": 363},
    "pacs.008": {"functionality": 440, "structure": 441, "constraints": 446, "blocks": 451},
    "pacs.009": {"functionality": 520, "structure": 521, "constraints": 528, "blocks": 535},
    "pacs.010": {"functionality": 653, "structure": 654, "constraints": 655, "blocks": 657},
    "pacs.028": {"functionality": 686, "structure": 687, "constraints": 690, "blocks": 692},
    
    "pain.001": {"functionality": 4, "structure": 6, "constraints": 10, "blocks": 14},
    "pain.002": {"functionality": 78, "structure": 79, "constraints": 84, "blocks": 87},
    "pain.007": {"functionality": 163, "structure": 164, "constraints": 168, "blocks": 171},
    "pain.008": {"functionality": 239, "structure": 240, "constraints": 244, "blocks": 246},
    
    "camt.026": {"functionality": 8, "structure": 10, "constraints": 17, "blocks": 19},
    "camt.027": {"functionality": 138, "structure": 140, "constraints": 146, "blocks": 148},
    "camt.028": {"functionality": 266, "structure": 268, "constraints": 277, "blocks": 279},
    "camt.029": {"functionality": 433, "structure": 435, "constraints": 451, "blocks": 455},
    "camt.030": {"functionality": 716, "structure": 718, "constraints": 719, "blocks": 719},
    "camt.031": {"functionality": 734, "structure": 735, "constraints": 736, "blocks": 736},
    "camt.032": {"functionality": 746, "structure": 747, "constraints": 747, "blocks": 748},
    "camt.033": {"functionality": 758, "structure": 759, "constraints": 759, "blocks": 760},
    "camt.034": {"functionality": 769, "structure": 770, "constraints": 770, "blocks": 771},
    "camt.035": {"functionality": 781, "structure": 782, "constraints": 782, "blocks": 783},
    "camt.036": {"functionality": 793, "structure": 794, "constraints": 794, "blocks": 795},
    "camt.037": {"functionality": 806, "structure": 808, "constraints": 814, "blocks": 816},
    "camt.038": {"functionality": 930, "structure": 931, "constraints": 931, "blocks": 932},
    "camt.039": {"functionality": 941, "structure": 943, "constraints": 944, "blocks": 944},
    "camt.055": {"functionality": 959, "structure": 961, "constraints": 966, "blocks": 969},
    "camt.056": {"functionality": 1057, "structure": 1060, "constraints": 1064, "blocks": 1067},
    "camt.087": {"functionality": 1144, "structure": 1147, "constraints": 1155, "blocks": 1157},
}
NEXT_MESSAGE_START_PAGE: Dict[str, int] = {
    "pacs.002": 79, "pacs.003": 145, "pacs.004": 353, "pacs.007": 440,
    "pacs.008": 520, "pacs.009": 653, "pacs.010": 686, "pacs.028": 743,
    "pain.001": 78, "pain.002": 163, "pain.007": 239, "pain.008": 309,
    "camt.026": 138, "camt.027": 266, "camt.028": 433, "camt.029": 716,
    "camt.030": 734, "camt.031": 746, "camt.032": 758, "camt.033": 769,
    "camt.034": 781, "camt.035": 793, "camt.036": 806, "camt.037": 930,
    "camt.038": 941, "camt.039": 959, "camt.055": 1057, "camt.056": 1144,
    "camt.087": 1291,
}
SECTION_ORDER = ["functionality", "structure", "constraints", "blocks"]
_PDF_CACHE: Dict[str, List[str]] = {}

# =====================================================
# FIX: Prevent GroupHeader <GrpHdr> building block spillover into child blocks
# =====================================================
GRPHDR_STOP_TAGS = [
    "<PmtInf>",
    "<CdtTrfTxInf>",
    "<DrctDbtTxInf>",
    "<Undrlyg>",
    "<Case>",
]

# =====================================================
# Utilities
# =====================================================

def _clean_pdf_text(text: str) -> str:
    """Clean PDF text and remove guideline / footer text"""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    text = re.sub(
        r'(?<!\n)\n(?!\n|\s*[•A-Z0-9<])',
        ' ',
        text
    )
    text = re.sub(r"\.{3,}", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove guideline sections
    text = re.sub(r'Guideline:.*?(?=\n[A-Z]|\n\nC\d+|$)', '', text, flags=re.DOTALL)

    # -------------------------------------------------
    # REMOVE PDF boilerplate (GLOBAL FIX)
    # -------------------------------------------------

    # Maintenance headers / footers
    text = re.sub(
        r'Payments\s+.*?Maintenance\s+\d{4}\s*-\s*\d{4}.*?(?:\n|$)',
        '',
        text,
        flags=re.IGNORECASE
    )

    # SEG approval lines
    text = re.sub(
        r'Approved\s+by\s+the\s+Payments\s+SEG.*?(?:\n|$)',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Message/version boilerplate lines
    text = re.sub(
        r'(pain|pacs|camt)\.\d{3}\.\d{3}\.\d+\s+.*?(?:\n|$)',
        '',
        text,
        flags=re.IGNORECASE
    )

    # Standalone month-year footers
    text = re.sub(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}',
        '',
        text,
        flags=re.IGNORECASE
    )

    return text.strip()
def _load_pdf_pages(path: str) -> List[str]:
    if path in _PDF_CACHE:
        return _PDF_CACHE[path]
    reader = PdfReader(path)
    pages: List[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            pages.append("")
    _PDF_CACHE[path] = pages
    return pages
def _get_section_page_bounds(message_code: str, section: str) -> Optional[Tuple[int, int]]:
    """
    Get page bounds for a section.
    CRITICAL FIX: For constraints and functionality, read until the NEXT section heading is found,
    not just until the page where next section starts.
    """
    if message_code not in SECTION_START_PAGES:
        return None
    section_pages = SECTION_START_PAGES[message_code]
    if section not in section_pages:
        return None
    
    start_page = section_pages[section]
    
    # CRITICAL FIX: For constraints and functionality, include next section start page for extraction
    # We'll filter by actual heading in get_pages_content()
    if section in ["constraints", "functionality"]:
        try:
            idx = SECTION_ORDER.index(section)
        except ValueError:
            return None
        
        if idx < len(SECTION_ORDER) - 1:
            next_section = SECTION_ORDER[idx + 1]
            next_start = section_pages.get(next_section, NEXT_MESSAGE_START_PAGE[message_code])
            # Include the next section's start page in extraction range
            end_page = next_start
        else:
            next_start = NEXT_MESSAGE_START_PAGE[message_code]
            end_page = next_start - 1
    else:
        # Normal logic for other sections
        try:
            idx = SECTION_ORDER.index(section)
        except ValueError:
            return None
        
        if idx < len(SECTION_ORDER) - 1:
            next_section = SECTION_ORDER[idx + 1]
            next_start = section_pages.get(next_section, NEXT_MESSAGE_START_PAGE[message_code])
        else:
            next_start = NEXT_MESSAGE_START_PAGE[message_code]
        
        end_page = next_start - 1
    
    return start_page, end_page
# =====================================================
# Extract message codes
# =====================================================
def extract_message_codes(query: str) -> List[str]:
    q = query.lower()
    matches = re.findall(r"\b(pain|pacs|camt)[\s.\-]?(\d{3})\b", q)
    codes: List[str] = []
    for prefix, num in matches:
        code = f"{prefix}.{num}"
        if code in MESSAGE_DEFINITIONS:
            codes.append(code)
    return list(dict.fromkeys(codes))
# =====================================================
# Intent Detection
# =====================================================
def detect_query_intent(query: str) -> Tuple[str, List[str], bool]:
    """
    Returns (intent, sections_to_fetch, wants_details)
    
    CRITICAL: For general questions about a message (what is X, purpose of X, when to use X, etc.)
    that don't explicitly ask for structure/constraints/building blocks,
    ALWAYS return 'functionality_full' intent to show complete MessageDefinition content.
    """
    q = query.lower()
    
    # =====================================================
    # STRUCTURE FIX (location-only)
    # If user asks for structure of a message, return ONLY the TOC-based
    # page location + PDF link (no table extraction, no LLM).
    # =====================================================
    if "structure" in q:
        return "structure_location", ["structure"], False

    # Location-only indicators
    location_indicators = ["where", "which page", "locate", "find"]
    wants_location_only = any(kw in q for kw in location_indicators) and \
                          not any(kw in q for kw in ["show", "give", "explain", "describe", "what is"])
    
    # EXPLICIT section requests (user specifically asks for these sections)
    
    # =====================================================
    # Message Building Blocks
    # =====================================================
    if any(kw in q for kw in ["message building block", "message building blocks", "building blocks"]):
        # If user mentions a specific block name or XML tag -> extract details
        if re.search(r'<[A-Za-z]+>', q) or any(
            kw in q for kw in ["assignment", "grouphdr", "case", "underlying", "justification"]
        ):
            return "specific_building_block", ["blocks"], True

        # Otherwise -> LOCATION ONLY (page + PDF)
        return "blocks_location", ["blocks"], False

    # Constraints (explicit or C-number based, e.g. C17)
    if any(kw in q for kw in ["constraint", "constraints", "rule", "rules"]) \
       or re.search(r"\bC\d+\b", q, flags=re.IGNORECASE):
       # If user asked for a specific constraint like C17
       if re.search(r"\bC\d+\b", q, flags=re.IGNORECASE):
           return "constraints", ["constraints"], True
       # GENERAL constraint queries → ALWAYS list all constraints
       return "constraints", ["constraints"], True
    
    # All details
    if any(kw in q for kw in ["everything", "complete", "all information"]):
        return "all", ["functionality", "structure", "constraints", "blocks"], True
    
    # Specific field queries (asking about a particular XML tag or field)
    specific_indicators = ["what is", "explain", "describe", "tell me about", "definition of", "show"]
    has_field_query = any(kw in q for kw in specific_indicators)
    has_message_code = any(code in q for code in MESSAGE_CODES)
    
    # Check if asking about a specific field/element (contains XML tag or specific term after "what is")
    has_specific_element = bool(re.search(r'<[A-Za-z]+>', q)) or \
                          (has_field_query and len([w for w in q.split() if w[0].isupper()]) > 1)
    
    if has_field_query and has_message_code and has_specific_element:
        return "specific_field", ["structure", "blocks", "constraints"], True
    
    # DEFAULT: General questions about the message
    return "functionality_full", ["functionality"], True
# =====================================================
# Term extraction
# =====================================================
def extract_search_terms(query: str) -> List[str]:
    """Extract constraint names, XML tags, field names, building block names"""
    candidates: List[str] = []
    q = query.strip()
    
    # XML tags like <Assgnmt>, <GrpHdr>
    tag_matches = re.findall(r"<([A-Za-z0-9]+)>", q)
    candidates.extend(tag_matches)
    
    # Uppercase terms: BICFI, C14, IBAN
    caps_matches = re.findall(r"\b[A-Z][A-Z0-9_]{1,}\b", q)
    candidates.extend(caps_matches)
    
    # Constraint codes: C14, C82
    constraint_matches = re.findall(r"\bC\d+\b", q, flags=re.IGNORECASE)
    candidates.extend([m.upper() for m in constraint_matches])
    
    # CamelCase words
    camel_case_matches = re.findall(r"\b([A-Z][a-z]+(?:[A-Z][a-z]*)*)\b", q)
    candidates.extend(camel_case_matches)
    
    # Compound names with spaces
    words = q.split()
    for i in range(len(words)):
        for length in range(2, 5):
            if i + length <= len(words):
                phrase = words[i:i+length]
                if all(word[0].isupper() for word in phrase if word):
                    compound = ''.join(word.capitalize() for word in phrase)
                    candidates.append(compound)
    
    return list(dict.fromkeys(candidates))

def find_term_in_section(
    message_code: str,
    section: str,
    search_terms: List[str],
    data_dir: Optional[str] = None
) -> Optional[Tuple[int, str, str]]:
    """
    Find page where term appears and extract content.
    Returns (page_number, extracted_content, matched_term) or None
    
    CRITICAL FIX: Improved building block matching to find exact element by XML tag.
    """
    if not search_terms:
        return None
        
    if data_dir is None:
        backend_root = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(backend_root, "data")
    
    prefix = message_code.split(".")[0]
    pdf_filename = MESSAGE_FILE_MAP.get(prefix)
    if not pdf_filename:
        return None
    
    pdf_path = os.path.join(data_dir, pdf_filename)
    if not os.path.exists(pdf_path):
        return None
    
    bounds = _get_section_page_bounds(message_code, section)
    if not bounds:
        return None
    
    start_page, end_page = bounds
    all_pages = _load_pdf_pages(pdf_path)

    def _page_window(start_num: int, max_pages: int = 3) -> str:
        """Return concatenated cleaned text for start page + following pages (handles page breaks)."""
        chunks = []
        last = min(start_num + max_pages - 1, end_page, len(all_pages))
        for p in range(start_num, last + 1):
            cleaned = _clean_pdf_text(all_pages[p - 1])
            if cleaned:
                chunks.append(cleaned)
        return "\n\n".join(chunks)

    for term in search_terms:
        term_lower = term.lower()
        
        for page_num in range(start_page, min(end_page + 1, len(all_pages) + 1)):
            page_text = all_pages[page_num - 1]
            page_text_clean = _clean_pdf_text(page_text)
            page_text_lower = page_text_clean.lower()
            
            # PATTERN 1: Constraint heading
            constraint_pattern = rf'\b{re.escape(term)}\s+[A-Z][a-zA-Z]+'
            if re.search(constraint_pattern, page_text_clean):
                match = re.search(constraint_pattern, page_text_clean)
                if match:
                    start_idx = match.start()
                    
                    # Look for next constraint OR "Message Building Blocks" heading
                    next_constraint = re.search(r'\nC\d+\s+[A-Z]', page_text_clean[start_idx+10:])
                    blocks_heading = re.search(
                        r'\n\s*\d+(?:\.\d+)*\s+Message\s+Building\s+Blocks',
                        page_text_clean[start_idx+10:],
                        re.IGNORECASE
                    )
                    
                    # Use whichever comes first
                    end_positions = []
                    if next_constraint:
                        end_positions.append(start_idx + 10 + next_constraint.start())
                    if blocks_heading:
                        end_positions.append(start_idx + 10 + blocks_heading.start())
                    
                    if end_positions:
                        end_idx = min(end_positions)
                    else:
                        end_idx = len(page_text_clean)
                    
                    extracted = page_text_clean[start_idx:end_idx]
                    return page_num, extracted, term
            
            # PATTERN 2: Building block heading with EXACT XML TAG MATCH
            # This is critical - we must match the EXACT XML tag to avoid confusion
            # e.g., "Assignment <Assgnmt>" should NOT match "Underlying <Undrlyg>"
            
            # Try exact numbered heading: "4.4.1 Assignment <Assgnmt>"
            exact_pattern = rf'(?mi)^\s*\d+(?:\.\d+)+\s+[A-Za-z\s]+<\s*{re.escape(term)}\s*>\s*$'
            exact_match = re.search(exact_pattern, page_text_clean, re.MULTILINE)
            
            if exact_match:
                # Build a multi-page window starting at the heading page, because
                # Definition/Usage often continues onto the next page in the PDF.
                window_text = _page_window(page_num, max_pages=3)
                start_idx = exact_match.start()

                # Find the next building block heading (numbered like "4.4.1.2 ... <Tag>")
                next_heading = re.search(
                    r'\n\s*\d+(?:\.\d+)+\s+[A-Z][A-Za-z0-9\s]+?\s*<[^>]+>',
                    window_text[start_idx + 1:],
                )

                if next_heading:
                    end_idx = start_idx + 1 + next_heading.start()
                else:
                    end_idx = min(len(window_text), start_idx + 8000)

                # Special handling for GroupHeader to prevent spillover into child blocks
                if term_lower in ['grphdr', 'groupheader']:
                    tail = window_text[start_idx:end_idx]
                    stop_positions = []
                    for _tag in GRPHDR_STOP_TAGS:
                        _m = re.search(re.escape(_tag), tail, re.IGNORECASE)
                        if _m:
                            stop_positions.append(_m.start())
                    if stop_positions:
                        end_idx = start_idx + min(stop_positions)

                extracted = window_text[start_idx:end_idx]
                print(f"[DEBUG] Found exact match for <{term}> on page {page_num}")
                return page_num, extracted, term
            
            # PATTERN 3: Without numbering but with exact XML tag
            simple_pattern = rf'(?mi)^\s*[A-Z][A-Za-z\s]+<\s*{re.escape(term)}\s*>\s*$'
            simple_match = re.search(simple_pattern, page_text_clean, re.MULTILINE)
            
            if simple_match:
                # Build a multi-page window starting at the heading page, because
                # Definition/Usage often continues onto the next page in the PDF.
                window_text = _page_window(page_num, max_pages=3)
                start_idx = simple_match.start()

                # Find next (possible) heading
                next_heading = re.search(
                    r'\n\s*\d*(?:\.\d+)*\s*[A-Z][A-Za-z0-9\s]+?\s*<[^>]+>',
                    window_text[start_idx + 1:],
                )

                if next_heading:
                    end_idx = start_idx + 1 + next_heading.start()
                else:
                    end_idx = min(len(window_text), start_idx + 8000)

                extracted = window_text[start_idx:end_idx]
                print(f"[DEBUG] Found simple match for <{term}> on page {page_num}")
                return page_num, extracted, term
    
    print(f"[DEBUG] No match found for terms: {search_terms}")
    return None

# =====================================================
# Content extraction - CRITICAL FIX FOR CONSTRAINTS AND FUNCTIONALITY
# =====================================================
def get_pages_content(message_code: str, section: str, data_dir: Optional[str] = None) -> str:
    """
    Extract FULL content from section.
    
    CRITICAL FIX: For constraints and functionality sections, stop at the next section heading,
    not at the page boundary. This ensures all content is captured even if it extends into 
    the page where the next section starts.
    """
    if data_dir is None:
        backend_root = os.path.dirname(os.path.dirname(__file__))
        data_dir = os.path.join(backend_root, "data")
    
    prefix = message_code.split(".")[0]
    pdf_filename = MESSAGE_FILE_MAP.get(prefix)
    if not pdf_filename:
        return ""
    
    pdf_path = os.path.join(data_dir, pdf_filename)
    if not os.path.exists(pdf_path):
        return ""
    
    bounds = _get_section_page_bounds(message_code, section)
    if not bounds:
        return ""
    
    start_page, end_page = bounds
    all_pages = _load_pdf_pages(pdf_path)
    
    # Special handling for constraints section
    if section == "constraints":
        full_text = ""
        for page_num in range(start_page - 1, min(end_page, len(all_pages))):
            cleaned = _clean_pdf_text(all_pages[page_num])
            if cleaned:
                full_text += "\n\n" + cleaned

        # 🔧 FIX: Start strictly from Constraints heading (e.g. "3.3 Constraints")
        m = re.search(r'^\s*\d+(?:\.\d+)*\s+Constraints\s*$', full_text, re.IGNORECASE | re.MULTILINE)
        if m:
            full_text = full_text[m.end():]

        # Find "Message Building Blocks" heading and stop there
        patterns = [
            r'\n\s*Message Building Blocks\s*\n',
            r'\n\s*MessageBuildingBlocks\s*\n',
            r'\n\s*Message\s+Building\s+Blocks\s*\n',
            r'^\s*\d+(?:\.\d+)*\s+Message\s+Building\s+Blocks',
            r'^\s*\d+(?:\.\d+)*\s+MessageBuildingBlocks',
        ]
        
        earliest_match_pos = len(full_text)
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            if match:
                earliest_match_pos = min(earliest_match_pos, match.start())
        
        if earliest_match_pos < len(full_text):
            return full_text[:earliest_match_pos].strip()
        
        return full_text.strip()
    
    # Special handling for functionality section
    if section == "functionality":
        full_text = ""
        for page_num in range(start_page - 1, min(end_page, len(all_pages))):
            cleaned = _clean_pdf_text(all_pages[page_num])
            if cleaned:
                full_text += "\n\n" + cleaned
        
        # Find "Structure" heading and stop there
        patterns = [
            r'\n\s*\d+(?:\.\d+)*\s+Structure\s*\n',
            r'\n\s*Structure\s*\n',
            r'^\s*\d+(?:\.\d+)*\s+Structure\s*$',
        ]
        
        earliest_match_pos = len(full_text)
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            if match:
                earliest_match_pos = min(earliest_match_pos, match.start())
        
        if earliest_match_pos < len(full_text):
            return full_text[:earliest_match_pos].strip()
        
        return full_text.strip()

    # Normal extraction for other sections
    parts: List[str] = []
    for page_num in range(start_page - 1, min(end_page, len(all_pages))):
        cleaned = _clean_pdf_text(all_pages[page_num])
        if cleaned:
            parts.append(cleaned)
    
    return "\n\n".join(parts)
# =====================================================
# Main Entry Point
# =====================================================
def answer_query(query: str) -> str:
    """Main entry point"""

    # =====================================================
    # Handle small talk / greetings BEFORE ISO logic
    # =====================================================
    if is_small_talk(query):
        return (
            "CHAT:SMALL_TALK|"
            "Hello! 😊 I'm doing well, thank you for asking.\n\n"
            "I can help you with ISO 20022 messages such as pain.001, pacs.004, camt.029 – "
            "including definitions, functionality, constraints, structure, and message building blocks.\n\n"
            "Whenever you're ready, just ask!"
        )

    codes = extract_message_codes(query)
    if not codes:
        return (
            "ERROR: NO_MESSAGE_CODE|"
            "I couldn't identify a specific ISO 20022 message code in your query. "
            "Please mention a message code like pacs.004, pain.001, or camt.029."
        )
    
    message_code = codes[0]
    intent, sections, wants_details = detect_query_intent(query)


    # =====================================================
    # MESSAGE BUILDING BLOCKS – location-only
    # =====================================================
    if intent == "blocks_location":
        response_parts: List[str] = []
        response_parts.append(f"MESSAGE_CODE:{message_code}")
        response_parts.append(f"DEFINITION:{MESSAGE_DEFINITIONS.get(message_code, '')}")

        prefix = message_code.split(".")[0]
        pdf_filename = MESSAGE_FILE_MAP.get(prefix, "")
        if pdf_filename:
            response_parts.append(f"PDF_FILE:{pdf_filename}")

        response_parts.append("QUERY_INTENT:blocks")
        response_parts.append("WANTS_DETAILS:false")

        blocks_page = SECTION_START_PAGES.get(message_code, {}).get("blocks")
        if blocks_page:
            response_parts.append(f"TARGET_PAGE:{blocks_page}")
            response_parts.append("TARGET_TERM:Message Building Blocks")

        response_parts.append("---CONTENT_START---")
        response_parts.append("---CONTENT_END---")
        return "\n".join(response_parts)

    
    # =====================================================
    # STRUCTURE FIX (location-only)
    # Return only TOC-based page number + metadata. No PDF extraction.
    # =====================================================
    if intent == "structure_location":
        response_parts: List[str] = []
        response_parts.append(f"MESSAGE_CODE:{message_code}")
        response_parts.append(f"DEFINITION:{MESSAGE_DEFINITIONS.get(message_code, '')}")

        prefix = message_code.split(".")[0]
        pdf_filename = MESSAGE_FILE_MAP.get(prefix, "")
        if pdf_filename:
            response_parts.append(f"PDF_FILE:{pdf_filename}")

        response_parts.append("QUERY_INTENT:structure")
        response_parts.append("WANTS_DETAILS:false")
        structure_page = SECTION_START_PAGES.get(message_code, {}).get("structure")
        if structure_page:
            response_parts.append(f"TARGET_PAGE:{structure_page}")
            response_parts.append("TARGET_TERM:Structure")

        response_parts.append("---CONTENT_START---")
        response_parts.append("---CONTENT_END---")
        return "\n".join(response_parts)

    response_parts: List[str] = []
    response_parts.append(f"MESSAGE_CODE:{message_code}")
    response_parts.append(f"DEFINITION:{MESSAGE_DEFINITIONS.get(message_code, '')}")
    
    prefix = message_code.split(".")[0]
    pdf_filename = MESSAGE_FILE_MAP.get(prefix, "")
    if pdf_filename:
        response_parts.append(f"PDF_FILE:{pdf_filename}")
    
    response_parts.append(f"QUERY_INTENT:{intent}")
    response_parts.append(f"WANTS_DETAILS:{'true' if wants_details else 'false'}")
    
    # Search for specific terms
    search_terms = extract_search_terms(query)
    target_info = None

    # Only attempt specific constraint lookup if query contains C<number>
    has_specific_constraint = bool(re.search(r"\bC\d+\b", query, flags=re.IGNORECASE))

    if has_specific_constraint and intent == "constraints":
        for section in sections:
            target_info = find_term_in_section(message_code, section, search_terms)
            if target_info:
                page_num, extracted, matched_term = target_info
                response_parts.append(f"TARGET_PAGE:{page_num}")
                response_parts.append(f"TARGET_TERM:{matched_term}")
                break

    # CRITICAL FIX: For building blocks, use find_term_in_section to get exact match
    if intent == "specific_building_block" and search_terms:
        print(f"[DEBUG] Searching for building block with terms: {search_terms}")
        for section in sections:
            target_info = find_term_in_section(message_code, section, search_terms)
            if target_info:
                page_num, extracted, matched_term = target_info
                response_parts.append(f"TARGET_PAGE:{page_num}")
                response_parts.append(f"TARGET_TERM:{matched_term}")
                print(f"[DEBUG] Found target on page {page_num}, term: {matched_term}")
                break
    
    # Section page ranges
    for section in sections:
        bounds = _get_section_page_bounds(message_code, section)
        if bounds:
            start_page, end_page = bounds
            response_parts.append(f"SECTION_PAGES:{section.upper()}:{start_page}-{end_page}")
    
    response_parts.append("---CONTENT_START---")
    
    if wants_details:
        if target_info:
            _, extracted, _ = target_info
            response_parts.append(f"##SECTION:EXTRACTED##")
            response_parts.append(extracted)
        else:
            for section in sections:
                content = get_pages_content(message_code, section)
                if content:
                    response_parts.append(f"##SECTION:{section.upper()}##")
                    response_parts.append(content)
    
    response_parts.append("---CONTENT_END---")
    
    return "\n".join(response_parts)
def index_documents(data_dir: Optional[str] = None) -> None:
    print("[RAG] Using direct PDF reading via TOC. No indexing needed.")