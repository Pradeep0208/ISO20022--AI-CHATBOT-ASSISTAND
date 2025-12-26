# app/main.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.rag_engine import answer_query, MESSAGE_CODES
import re


from ollama import Client
from huggingface_hub import InferenceClient
import os

# =====================================================
# FastAPI App
# =====================================================

app = FastAPI(title="ISO 20022 Learning Chatbot API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str

# =====================================================
# Ollama Client
# =====================================================

ollama_client = Client(host=OLLAMA_HOST)

hf_client = InferenceClient(model=HF_MODEL, token=HF_TOKEN) if HF_TOKEN else None
MODEL_NAME = "llama3.2:latest"

# --- Deployment configuration (Local vs Hugging Face Spaces) ---
# Local dev: uses Ollama running on your machine.
# Hugging Face Spaces: Ollama is usually NOT available, so we use HF Inference API instead.
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", MODEL_NAME)

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
HF_MAX_NEW_TOKENS = int(os.getenv("HF_MAX_NEW_TOKENS", "512"))
HF_TEMPERATURE = float(os.getenv("HF_TEMPERATURE", "0.2"))

# HF sets SPACE_ID automatically in Spaces runtime
RUNNING_ON_SPACES = bool(os.getenv("SPACE_ID"))

def run_llm(prompt: str) -> str:
    try:
        response = ollama_client.generate(
            model=MODEL_NAME,
            prompt=prompt,
            stream=False
        )
        return response.get("response", "").strip()
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return None



# =====================================================
# Deterministic constraint formatting (NO LLM)
# =====================================================

_CONSTRAINT_BLOCK_RE = re.compile(
    r'(?m)^\s*(?:•\s*)?(C\d+)\s*([^\n]*)\n(.*?)(?=^\s*(?:•\s*)?C\d+\s|\Z)',
    re.DOTALL
)



# -------------------------------------------------
# Strip stray PDF footer page numbers that appear as standalone lines
# (e.g., "157") inside extracted CONSTRAINTS text.
# We only apply this cleanup inside constraint blocks to avoid impacting
# other sections like Structure tables.
# -------------------------------------------------
_STANDALONE_PAGE_NUM_RE = re.compile(r'(?m)^\s*\d{1,4}\s*$')

def _strip_standalone_page_numbers(s: str) -> str:
    if not s:
        return ""
    s = _STANDALONE_PAGE_NUM_RE.sub("", s)
    # Collapse excessive blank lines created by the removal
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

def _format_all_constraints_exact(text: str) -> str:
    """Return all constraints exactly as in PDF content (no hallucinations)."""
    matches = _CONSTRAINT_BLOCK_RE.findall((text or "").strip())
    if not matches:
        return (text or "").strip()

    out = []
    for code, name, body in matches:
        body = _strip_standalone_page_numbers(body)
        if not body:
            continue
        name = name.strip()
        title = f"**{code} {name}**" if name else f"**{code}**"
        out.append(f"{title}\n{body}")
    return "\n\n".join(out)

def _extract_specific_constraint_exact(text: str, target: str) -> str:
    """Return one constraint block (e.g., C17) exactly as in PDF content."""
    target = (target or "").strip().upper()
    if not target:
        return ""

    # Search for the specific block by code
    pattern = re.compile(
        rf'(?m)^\s*(?:•\s*)?({re.escape(target)})\s*([^\n]*)\n(.*?)(?=^\s*(?:•\s*)?C\d+\s|\Z)',
        re.DOTALL
    )
    m = pattern.search((text or "").strip())
    if not m:
        return f"Constraint {target} not found in the PDF."

    code, name, body = m.group(1), m.group(2).strip(), _strip_standalone_page_numbers(m.group(3))
    title = f"**{code} {name}**" if name else f"**{code}**"
    return f"{title}\n{body}"


# =====================================================
# Deterministic building-block extraction (NO LLM)
# =====================================================

_BLOCK_HEADING_RE = re.compile(
    r'(?mi)^\s*(\d+(?:\.\d+)*\s+)?(?P<name>[A-Za-z][A-Za-z0-9\s]+?)\s*<(?P<tag>[A-Za-z0-9]+)>\s*$'
)

_NEXT_BLOCK_RE = re.compile(
    r'(?mi)^\s*\d+(?:\.\d+)*\s+[A-Za-z][A-Za-z0-9\s]+?\s*<[^>]+>\s*$'
)

def _extract_building_block_snippet(blocks_text: str, *, xml_tag: str = "", element_name: str = "", max_chars: int = 8000) -> str:
    """
    Extract a single building-block chunk from the full BLOCKS section text.
    Uses either the XML tag (<GrpHdr>) or the element name (GroupHeader) to locate the block.
    
    IMPROVED: More flexible matching patterns and better boundary detection.
    """
    if not blocks_text:
        return ""

    t = blocks_text

    # Prefer XML tag match (most reliable)
    start_idx = -1
    if xml_tag:
        # Pattern 1: Full heading with numbering: "3.4.1 GroupHeader <GrpHdr>"
        tag_pat = re.compile(rf'(?mi)^\s*\d+(?:\.\d+)*\s+.*?<\s*{re.escape(xml_tag)}\s*>\s*$', re.MULTILINE)
        m = tag_pat.search(t)
        if m:
            start_idx = m.start()
        
        # Pattern 2: Without numbering: "GroupHeader <GrpHdr>"
        if start_idx < 0:
            tag_pat2 = re.compile(rf'(?mi)^\s*[A-Z][A-Za-z]+\s*<\s*{re.escape(xml_tag)}\s*>\s*$', re.MULTILINE)
            m = tag_pat2.search(t)
            if m:
                start_idx = m.start()

    # Fallback: element name match
    if start_idx < 0 and element_name:
        # Try exact element name with XML tag
        name_pat = re.compile(rf'(?mi)^\s*\d*(?:\.\d+)*\s*{re.escape(element_name)}\s*<[^>]+>\s*$', re.MULTILINE)
        m = name_pat.search(t)
        if m:
            start_idx = m.start()
        
        # Try element name without requiring full structure
        if start_idx < 0:
            name_pat2 = re.compile(rf'(?mi)^\s*{re.escape(element_name)}\s*<[^>]+>', re.MULTILINE)
            m = name_pat2.search(t)
            if m:
                start_idx = m.start()

    # Final fallback: look for "<Tag>" anywhere (less strict)
    if start_idx < 0 and xml_tag:
        m = re.search(rf'<\s*{re.escape(xml_tag)}\s*>', t, flags=re.IGNORECASE)
        if m:
            # Back up to try to include the heading line
            start_idx = max(0, m.start() - 200)

    if start_idx < 0:
        return ""

    tail = t[start_idx:]

    # Stop at next block heading
    nxt = _NEXT_BLOCK_RE.search(tail[1:])
    end_idx = start_idx + (1 + nxt.start()) if nxt else min(len(t), start_idx + max_chars)

    return t[start_idx:end_idx].strip()

def _parse_definition_usage(snippet: str) -> tuple[str, str]:
    """
    Parse Definition and Usage from a block snippet.
    Returns (definition, usage) where either may be "".
    
    IMPROVED: Better pattern matching for Definition and Usage sections.
    """
    if not snippet:
        return "", ""

    # Normalize spacing
    s = snippet.replace("\r\n", "\n").replace("\r", "\n")

    # Capture Definition with improved pattern
    def_patterns = [
        r'(?mi)^\s*Definition:\s*(.+?)(?=\n\s*Usage:|\n\s*Datatype:|\n\s*Presence:|\n\s*\d+(?:\.\d+)*\s+[A-Z].*?<|$)',
        r'(?mi)Definition:\s*(.+?)(?=\nUsage:|\nDatatype:|\nPresence:|\n\d+(?:\.\d+)*\s+[A-Z]|$)',
    ]
    
    definition = ""
    for pattern in def_patterns:
        def_m = re.search(pattern, s, flags=re.DOTALL)
        if def_m:
            definition = def_m.group(1).strip()
            break

    # Capture Usage with improved pattern
    use_patterns = [
        r'(?mi)^\s*Usage:\s*(.+?)(?=\n\s*Datatype:|\n\s*Presence:|\n\s*\d+(?:\.\d+)*\s+[A-Z].*?<|$)',
        r'(?mi)Usage:\s*(.+?)(?=\nDatatype:|\nPresence:|\n\d+(?:\.\d+)*\s+[A-Z]|$)',
    ]
    
    usage = ""
    for pattern in use_patterns:
        use_m = re.search(pattern, s, flags=re.DOTALL)
        if use_m:
            usage = use_m.group(1).strip()
            break

    # Clean bullet artifacts and normalize whitespace
    definition = re.sub(r'\s+', ' ', definition).strip()
    usage = re.sub(r'\s+', ' ', usage).strip()

    return definition, usage

def _extract_messageelement_tags(snippet: str) -> list[str]:
    """
    Extract XML tags listed in MessageElement<XML Tag> rows within the snippet.
    Returns unique tags in appearance order.
    """
    if not snippet:
        return []

    tags = []
    seen = set()

    # Match rows like: MessageIdentification <MsgId>
    for m in re.finditer(r'([A-Za-z][A-Za-z0-9]+)\s*<\s*([A-Za-z0-9]+)\s*>', snippet):
        tag = m.group(2)
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags

def _extract_xml_tag_from_query(query: str) -> str:
    """Extract XML tag from user query (e.g., <MsgId> from the query)"""
    xml_m = re.search(r"<\s*([A-Za-z0-9]+)\s*>", query)
    if xml_m:
        return xml_m.group(1)
    return ""

def _extract_element_name_from_query(query: str, message_code: str) -> str:
    """
    Extract element name from query by removing common question words and message code.
    Returns clean element name (e.g., "GroupHeader", "MessageIdentification")
    """
    # Remove common question patterns
    cleaned = query
    question_patterns = [
        r"(?i)\b(what is|show|explain|describe|tell me about|give me|find)\b",
        r"(?i)\bmessage building blocks?\b",
        r"(?i)\bin\b",
        r"(?i)\bfor\b",
        r"(?i)\bof\b",
        message_code,
    ]
    
    for pattern in question_patterns:
        cleaned = re.sub(pattern, "", cleaned)
    
    # Remove XML tags to get element name
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    
    # Clean up and get CamelCase words or significant terms
    cleaned = cleaned.strip()
    
    # Try to find CamelCase word (most reliable)
    camel_match = re.search(r'\b([A-Z][a-z]+(?:[A-Z][a-z]*)+)\b', cleaned)
    if camel_match:
        return camel_match.group(1)
    
    # Otherwise take remaining meaningful text
    words = [w for w in cleaned.split() if len(w) > 2 and not w.lower() in ['the', 'and', 'this', 'that']]
    if words:
        return ''.join(w.capitalize() for w in words)
    
    return ""

def enhance_with_llm(raw_content: str, user_query: str) -> str:
    """Transform PDF content with page numbers and download links"""

    # =====================================================
    # Handle small talk responses (no ISO formatting)
    # =====================================================
    if raw_content.startswith("CHAT:SMALL_TALK|"):
        return raw_content.split("|", 1)[1].strip()
    
    if raw_content.startswith("ERROR:"):
        return raw_content.split("|")[1]
    
    # Parse structured response
    lines = raw_content.split("\n")
    message_code = ""
    definition = ""
    intent = ""
    pdf_file = ""
    wants_details = True
    target_page = None
    target_term = ""
    section_pages = {}
    content_sections = {}
    
    current_section = None
    section_content = []
    in_content = False
    
    for line in lines:
        if line.startswith("MESSAGE_CODE:"):
            message_code = line.split(":", 1)[1]
        elif line.startswith("DEFINITION:"):
            definition = line.split(":", 1)[1]
        elif line.startswith("PDF_FILE:"):
            pdf_file = line.split(":", 1)[1]
        elif line.startswith("QUERY_INTENT:"):
            intent = line.split(":", 1)[1]
        elif line.startswith("WANTS_DETAILS:"):
            wants_details = line.split(":", 1)[1] == "true"
        elif line.startswith("TARGET_PAGE:"):
            target_page = int(line.split(":", 1)[1])
        elif line.startswith("TARGET_TERM:"):
            target_term = line.split(":", 1)[1]
        elif line.startswith("SECTION_PAGES:"):
            parts = line.split(":", 2)
            if len(parts) == 3:
                section_name = parts[1]
                page_range = parts[2]
                section_pages[section_name] = page_range
        elif line == "---CONTENT_START---":
            in_content = True
        elif line == "---CONTENT_END---":
            if current_section and section_content:
                content_sections[current_section] = "\n".join(section_content)
            break
        elif in_content and line.startswith("##SECTION:"):
            if current_section and section_content:
                content_sections[current_section] = "\n".join(section_content)
            current_section = line.replace("##SECTION:", "").replace("##", "").strip()
            section_content = []
        elif in_content and current_section:
            section_content.append(line)
    
    # Build page reference
    page_ref = ""
    if target_page:
        page_ref = f"**📍 Page: {target_page}**"
    elif section_pages:
        ranges = [f"{k}: pages {v}" for k, v in section_pages.items()]
        page_ref = f"**📍 Sections:** {', '.join(ranges)}"
    
    # Build download link
    download_link = f"📄 Download PDF: http://localhost:8000/pdfs/{pdf_file}"
    
    # Handle location-only
    if not wants_details:
        return f"**{message_code}**\n\n{definition}\n\n{page_ref}\n\n{download_link}\n\n💡 *Open the link above to view the detailed content in the PDF.*"
    
    # No content extracted
    if not content_sections:
        return f"**{message_code}**\n\n{definition}\n\n{page_ref}\n\n{download_link}\n\nNo detailed content extracted. Please refer to the PDF."
    
    

    # =====================================================
    # CRITICAL FIX: Constraints must be deterministic (NO LLM)
    # Applies to ALL pain / pacs / camt messages.
    # =====================================================
    if intent == "constraints":
        # Only treat C## as specific constraints
        if target_term and re.fullmatch(r"C\d+", target_term):
            src = content_sections.get("EXTRACTED", "") or content_sections.get("CONSTRAINTS", "")
            result = _extract_specific_constraint_exact(src, target_term)
        else:
            src = content_sections.get("CONSTRAINTS", "")
            result = _format_all_constraints_exact(src)

        footer = f"\n\n---\n\n{page_ref}\n\n{download_link}"
        return result + footer
# =====================================================
    # =====================================================
    # CRITICAL FIX: Handle functionality_full intent
    # =====================================================
    if intent == "functionality_full":
        # For general questions, return COMPLETE MessageDefinition - Functionality
        # Use deterministic formatting (NO LLM to avoid truncation)
        func_content = content_sections.get("FUNCTIONALITY", "")
        
        if not func_content:
            return f"**{message_code}**\n\n{definition}\n\n{page_ref}\n\n{download_link}\n\nNo functionality content found."
        
        # Deterministic formatting with bold headings
        formatted_content = func_content

        # -------------------------------------------------
        # REMOVE PDF boilerplate (approval / maintenance)
        # -------------------------------------------------
        formatted_content = re.sub(
            r'Approved by the Payments SEG.*?(?:\n|$)',
            '',
            formatted_content,
            flags=re.IGNORECASE
        )
        formatted_content = re.sub(
            r'Exceptions and Investigations\s*-\s*Maintenance.*?(?:\n|$)',
            '',
            formatted_content,
            flags=re.IGNORECASE
        )

        # -------------------------------------------------
        # Improve spacing for readability (presentation only)
        # -------------------------------------------------
        formatted_content = re.sub(
            r'\n(Scope|Usage|Outline)\n',
            r'\n\n\1\n',
            formatted_content
        )
        formatted_content = re.sub(
            r'\n([A-E]\.\s)',
            r'\n\n\1',
            formatted_content
        )

        # -------------------------------------------------
        # Make specific headings bold
        # -------------------------------------------------
        formatted_content = re.sub(
            r'(^|\n)(MessageDefinition Functionality|Scope|Usage|Outline)(\s*\n)',
            r'\1**\2**\3',
            formatted_content,
            flags=re.MULTILINE
        )

        # Also bold "The UnableToApply message:" heading
        formatted_content = re.sub(
            r'(^|\n)(The UnableToApply message:)(\s*\n)',
            r'\1**\2**\3',
            formatted_content,
            flags=re.MULTILINE
        )
# Build response with message header
        result = f"**{message_code}**\n\n{definition}\n\n{formatted_content}"
        
        # Add footer
        footer = f"\n\n---\n\n{page_ref}\n\n{download_link}"
        return result + footer
    
    # =====================================================
    # CRITICAL FIX: Building Blocks - Improved Extraction
    # =====================================================
    if intent == "specific_building_block":
        blocks_content = content_sections.get("EXTRACTED", content_sections.get("BLOCKS", "")) or ""

        # Extract XML tag and element name from query
        xml_tag = _extract_xml_tag_from_query(user_query)
        element_name = _extract_element_name_from_query(user_query, message_code)

        print(f"[DEBUG] Building block search - XML Tag: '{xml_tag}', Element Name: '{element_name}'")

        # Try deterministic extraction
        snippet = _extract_building_block_snippet(blocks_content, xml_tag=xml_tag, element_name=element_name)

        if snippet:
            print(f"[DEBUG] Found snippet (length: {len(snippet)})")
            definition_text, usage_text = _parse_definition_usage(snippet)

            # Try to build a nice title from the snippet heading
            title = ""
            head_m = re.search(r'(?mi)^\s*\d*(?:\.\d+)*\s*(.+?<[^>]+>)\s*$', snippet, re.MULTILINE)
            if head_m:
                title = head_m.group(1).strip()
            elif xml_tag and element_name:
                title = f"{element_name} <{xml_tag}>"
            elif xml_tag:
                title = f"<{xml_tag}>"
            elif element_name:
                title = element_name
            else:
                title = "Requested element"

            # If we found at least Definition or Usage, return deterministically
            if definition_text or usage_text:
                out_lines = [f"**{title}**", ""]

                # Remove PDF approval / maintenance boilerplate
                definition_text = re.sub(
                    r'Approved by the Payments SEG.*?(?:\n|$)',
                    '',
                    definition_text,
                    flags=re.IGNORECASE
                )
                usage_text = re.sub(
                    r'Approved by the Payments SEG.*?(?:\n|$)',
                    '',
                    usage_text,
                    flags=re.IGNORECASE
                )
                definition_text = re.sub(
                    r'Exceptions and Investigations\s*-\s*Maintenance.*?(?:\n|$)',
                    '',
                    definition_text,
                    flags=re.IGNORECASE
                )
                usage_text = re.sub(
                    r'Exceptions and Investigations\s*-\s*Maintenance.*?(?:\n|$)',
                    '',
                    usage_text,
                    flags=re.IGNORECASE
                )

                if definition_text:
                    out_lines.append(f"• **Definition:** {definition_text}")
                    out_lines.append("")
                if usage_text:
                    out_lines.append(f"• **Usage:** {usage_text}")
                    out_lines.append("")

                footer = f"---\n\n{page_ref}\n\n{download_link}"
                return "\n".join(out_lines).strip() + "\n\n" + footer

        # Deterministic extraction failed - fall back to LLM with improved prompt
        print(f"[DEBUG] Deterministic extraction failed, falling back to LLM")
        
        # Build clear search term for LLM
        search_term = xml_tag if xml_tag else element_name if element_name else "the requested element"
        
        prompt = f"""You are an ISO 20022 expert. Extract building block element information.

USER ASKED ABOUT: {search_term} in {message_code}
ORIGINAL QUERY: {user_query}

PDF CONTENT:
{(blocks_content or "")[:15000]}

CRITICAL INSTRUCTIONS:
1. Find the element that matches: {search_term}
2. Look for a heading like "ElementName <Tag>" or just the tag "<{xml_tag}>" if provided
3. Extract ONLY what EXISTS in the PDF:
   • **Definition:** (if present - extract the complete definition text)
   • **Usage:** (ONLY if present - do NOT infer or reuse from other elements)

4. Format your response EXACTLY like this:
   ElementName <Tag>

   • **Definition:** [exact definition text from PDF]

   • **Usage:** [exact usage text from PDF - ONLY if it exists]

5. DO NOT include:
   - MessageElement XML tags list
   - Explanations or interpretations
   - Content from other elements
   - Made-up information

6. If the element is not found, respond ONLY with:
   "Element '{search_term}' not found in {message_code} message building blocks."

Provide the response:"""

        result = run_llm(prompt)
        
        if not result:
            return f"**{message_code}**\n\n{definition}\n\n{page_ref}\n\n{download_link}\n\nUnable to extract building block information."
        
        # Add footer
        footer = f"\n\n---\n\n{page_ref}\n\n{download_link}"
        return result + footer

    # =====================================================
    # Handle other intents with existing logic
    # =====================================================
    
    # Build LLM prompts based on intent
    if intent == "constraints" and target_term:
        # Specific constraint
        extracted_content = content_sections.get("EXTRACTED", "")
        if not extracted_content:
            extracted_content = "\n\n".join(content_sections.values())
        
        prompt = f"""You are an ISO 20022 expert. Extract constraint information from the PDF content.

CONSTRAINT: {target_term} in {message_code}

PDF CONTENT:
{extracted_content[:4000]}

CRITICAL INSTRUCTIONS:
1. Find the constraint "{target_term}"
2. Extract ONLY what's in the PDF:
   - Constraint name/code
   - Definition (exact wording)
   - Usage rules (exact wording)
   - Related MessageElement XML tags if mentioned
3. Format clearly with the constraint name as heading
4. DO NOT add explanations, interpretations, or additional text
5. DO NOT say "unfortunately" or "I was unable to find" - just present what you found
6. If the constraint is clearly defined, present it directly
7. Keep exact wording from PDF

Provide the response (constraint info only):"""

    elif intent == "constraints":
        # All constraints
        constraint_content = content_sections.get("CONSTRAINTS", "")
        prompt = f"""You are an ISO 20022 expert. List all constraints from the PDF.

MESSAGE: {message_code}

PDF CONTENT:
{constraint_content}

CRITICAL INSTRUCTIONS:
1. List ALL constraints found (C1, C2, C3... up to C82 or however many exist)
2. Format each as:
   **C## ConstraintName**
   [Exact definition from PDF]

3. DO NOT skip constraints - include every single one
4. DO NOT add guideline text or light font text
5. Keep exact wording from PDF
6. If a constraint has no description, skip it
7. DO NOT truncate - list ALL constraints

Provide the complete list:"""

    elif intent == "structure":
        structure_content = content_sections.get("STRUCTURE", "")
        prompt = f"""You are an ISO 20022 expert. Present message structure.

MESSAGE: {message_code}

PDF CONTENT:
{structure_content[:15000]}

INSTRUCTIONS:
1. Show structure with XML tags and cardinality
2. Extract MessageElement column only from tables
3. Keep hierarchy
4. Format clearly
5. DO NOT add explanations

Provide the response:"""

    elif intent == "blocks":
        blocks_content = content_sections.get("BLOCKS", "")
        prompt = f"""You are an ISO 20022 expert. Present building blocks.

MESSAGE: {message_code}

PDF CONTENT:
{blocks_content[:15000]}

INSTRUCTIONS:
1. List building blocks with names and cardinality
2. Brief description for each
3. Keep exact wording

Provide the response:"""

    elif intent == "specific_field":
        all_content = "\n\n".join(content_sections.values())
        
        field_keywords = ["what is", "explain", "describe", "tell me about", "show"]
        field_name = user_query.lower()
        for kw in field_keywords:
            if kw in field_name:
                field_name = field_name.split(kw)[1].strip()
                break
        
        for code in MESSAGE_CODES:
            field_name = field_name.replace(code, "").replace("in", "").replace("for", "").strip()
        
        prompt = f"""You are an ISO 20022 expert. Find specific field information.

FIELD: {field_name} in {message_code}

PDF CONTENT:
{all_content[:15000]}

INSTRUCTIONS:
1. Search for "{field_name}"
2. If found: XML tag, cardinality, definition
3. Extract MessageElement only from tables
4. If NOT found: "Could not find '{field_name}' in {message_code}."

Provide the response:"""

    else:
        # Fallback - should not reach here with new intent logic
        func_content = content_sections.get("FUNCTIONALITY", "")
        prompt = f"""You are an ISO 20022 expert. Present the COMPLETE MessageDefinition - Functionality.

MESSAGE: {message_code}
DEFINITION: {definition}

PDF CONTENT:
{func_content}

INSTRUCTIONS:
1. Present COMPLETE content - DO NOT summarize
2. Include Scope, Usage, Outline from PDF
3. Use bullet points where appropriate
4. Keep exact wording

Provide the complete response:"""

    # Call LLM
    if len(prompt) > 20000:
        prompt = prompt[:20000] + "\n\n[Truncated]"
    
    result = run_llm(prompt)
    
    if not result:
        fallback = f"**{message_code}**\n\n{definition}\n\n"
        if content_sections:
            for section, content in list(content_sections.items())[:2]:
                fallback += f"\n### {section}\n{content[:1000]}...\n"
        fallback += f"\n{page_ref}\n\n{download_link}"
        return fallback
    
    # Check for hallucination
    if any(word in result.lower() for word in ["mt104", "mt103", "swift mt"]):
        result = f"**{message_code}**\n\n{definition}\n\nPlease refer to the PDF.\n\n{page_ref}\n\n{download_link}"
        return result
    
    # Add footer
    footer = f"\n\n---\n\n{page_ref}\n\n{download_link}"
    return result + footer

# =====================================================
# Startup
# =====================================================

@app.on_event("startup")
def startup_event():
    print("=" * 60)
    print("ISO 20022 Learning Chatbot API")
    print("=" * 60)

# =====================================================
# PDF Download Endpoint
# =====================================================

@app.get("/pdfs/{filename}")
def download_pdf(filename: str):
    """Serve PDF files"""
    backend_root = os.path.dirname(os.path.dirname(__file__))
    pdf_path = os.path.join(backend_root, "data", filename)
    
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf", filename=filename)
    else:
        return {"error": "PDF not found"}

# =====================================================
# Main Chat Endpoint
# =====================================================

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    raw_content = answer_query(request.query)
    final_answer = enhance_with_llm(raw_content, request.query)
    return ChatResponse(answer=final_answer)



# --- Serve built frontend (for Hugging Face Spaces / single-link deployments) ---
# If you build the React app into /frontend/dist, FastAPI will serve it as a static website.
try:
    from pathlib import Path
    FRONTEND_DIST = (Path(__file__).resolve().parents[2] / "frontend" / "dist")
    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
except Exception:
    # Ignore if dist isn't built yet (common during local dev)
    pass
