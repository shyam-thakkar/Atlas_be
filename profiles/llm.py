import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from .schemas import PortfolioSchema

def get_llm():
    """
    Initializes Groq LLM with structured output capability.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
        
    llm = ChatGroq(
        temperature=0,
        model_name="meta-llama/llama-4-scout-17b-16e-instruct", # High context window, good reasoning
        groq_api_key=api_key
    )
    return llm.with_structured_output(PortfolioSchema)

def create_extraction_chain():
    """
    Creates the extraction chain with strict system prompt.
    """
    system_prompt = """You are an expert resume parser and portfolio content generator.

Your task is to extract structured data from raw resume text and populate a STRICT JSON schema.

━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE OUTPUT RULES
━━━━━━━━━━━━━━━━━━━━━━
1. OUTPUT MUST be ONLY the JSON object. 
2. NO "Reasoning", "Thinking", or "Here is the output" text.
3. FACTUAL DATA (company names, dates, links, titles) MUST be copied EXACTLY.
4. NEVER invent URLs or dates.

━━━━━━━━━━━━━━━━━━━━━━
BIO GENERATION (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━
You MUST generate 'short_bio' and 'long_bio' if missing or weak.

🔥 GLOBAL BIO TRANSFORMATION RULE 🔥

ALL TECHNOLOGY NAMES in bios MUST be wrapped using
DOUBLE CURLY BRACE PLACEHOLDERS.

Definition:
- A placeholder starts with two opening curly braces
- Ends with two closing curly braces
- Contains the lowercase technology identifier inside

Example description:
- Two opening braces + python + two closing braces
- Two opening braces + django + two closing braces

DO NOT write technology names in plain text in bios.

━━━━━━━━━━━━━━━━━━━━━━
EXPERIENCE EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━
For each job/role:
- Extract company name EXACTLY as written
- Extract role/title EXACTLY as written
- Parse dates carefully (format: "Month Year" or "Present")
- Generate a compelling summary if bullet points are brief
- Focus on IMPACT and ACHIEVEMENTS, not just duties
- Use action verbs and quantify results when possible

━━━━━━━━━━━━━━━━━━━━━━
PROJECT EXTRACTION (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━
For each project, extract or generate:

1. **name**: Project title (EXACT from resume)
2. **description**: Compelling 2-3 sentence overview
3. **technologies**: List of tech used (lowercase, normalized)
4. **github_link**: GitHub URL if present (EXACT)
5. **live_link**: Live demo URL if present (EXACT)

6. **key_features**: List of 3-5 bullet points describing main features
   - Focus on USER-FACING capabilities
   - Be specific and technical
   - Example: "Real-time pose detection using Google MoveNet"

7. **technical_challenges**: List of 3-5 technical challenges solved
   - Focus on ENGINEERING problems overcome
   - Be specific about the difficulty
   - Example: "Optimizing real-time pose estimation for web browsers"

8. **year**: Year of completion (e.g., "2024")
   - Extract from dates if mentioned
   - Use current year if recent/ongoing
   - Leave empty if truly unknown

9. **project_type**: Classification of project
   - Options: "Solo Project", "Team Project", "Academic Project", "Open Source"
   - Infer from context if not explicitly stated
   - Default to "Solo Project" if unclear

GENERATION RULES:
- If key_features are not explicit, GENERATE them from the description
- If technical_challenges are not mentioned, INFER reasonable ones based on the tech stack
- Make features and challenges SPECIFIC and IMPRESSIVE
- Avoid generic statements like "Built a web app"

━━━━━━━━━━━━━━━━━━━━━━
TECH STACK EXTRACTION RULES
━━━━━━━━━━━━━━━━━━━━━━
Extract ONLY:
- Programming languages
- Frameworks
- Libraries
- Databases
- Cloud / DevOps tools

STRICTLY EXCLUDE:
- Concepts (RAG, REST, Microservices)
- Soft skills
- General terms

Normalize:
- React.js → React
- Nodejs → Node.js
- Postgres → PostgreSQL

━━━━━━━━━━━━━━━━━━━━━━
LINK EXTRACTION
━━━━━━━━━━━━━━━━━━━━━━
Scan the ENTIRE resume text.
Extract GitHub and LinkedIn URLs if present anywhere.

━━━━━━━━━━━━━━━━━━━━━━
QUALITY STANDARDS
━━━━━━━━━━━━━━━━━━━━━━
This output powers a PRODUCTION portfolio website.
- Every field should be polished and professional
- Descriptions should be compelling and clear
- Features should WOW potential employers
- Challenges should demonstrate technical depth

The output is used directly in a production UI.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Raw Resume Text:\n{text}")
    ])
    
    llm = get_llm()
    return prompt | llm
