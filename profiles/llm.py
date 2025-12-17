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
    system_prompt = """You are an expert resume parser for a developer portfolio website.
    Your task is to extract structured data from the provided raw resume text to populate a strictly defined JSON schema.

    CRITICAL RULES:
    1. Input is raw resume text. Output MUST strictly follow the schema.
    2. Empty string ("") or empty list ([]) is allowed if factual data (links, dates) is missing.
    3. FACTUAL DATA (Dates, Links, Company Names, Job Titles) must be exact. DO NOT invent these.
    4. CREATIVE WRITING ALLOWED for Bios and Descriptions:
       - If 'short_bio', 'long_bio', or project/experience 'descriptions' are missing or weak, GENERATE them based on the resume context.
       - Write in a professional, engaging developer portfolio style (1st or 3rd person consistent).
       - highlighting key skills and achievements found in the text.
    5. NEVER infer links. Only extract explicit URLs.
    6. NEVER guess dates. Use the exact text provided or standard formats if unambiguous.
    7. Social Links (AGGRESSIVE SEARCH): 
       - Scan the ENTIRE text for GitHub and LinkedIn URLs. 
       - Extract them even if they are just plain text or hidden in contact info.
       - 'github' and 'linkedin' fields MUST be populated if a URL exists anywhere in the text.
    8. Tech Stack (STRICT CATEGORY FILTERING): 
       - EXTRACT ONLY: Concrete Programming Languages (Python, Java), Frameworks (React, Django), Libraries (NumPy), Databases (PostgreSQL), Developer Tools (Docker, AWS).
       - STRICTLY EXCLUDE: 
         - Concepts/Techniques: "RAG", "Prompt Engineering", "Vector Embeddings", "Microservices", "REST API", "CI/CD", "Agile", "Scrum".
         - Soft Skills: "Leadership", "Communication".
         - General Terms: "Web Development", "Data Science".
       - NORMALIZE: "React.js"->"React", "Nodejs"->"Node.js", "Postgres"->"PostgreSQL".
       - OUTPUT: Flat list of clean, iconic tool names only.
    9. FORMATTING: 'summary' and 'description' fields MUST be single strings. if you have bullet points, join them with newlines or spaces. DO NOT return arrays for these fields.

    The output will be used directly in a UI, so ensure clean, professional formatting.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Raw Resume Text:\n{text}")
    ])
    
    llm = get_llm()
    return prompt | llm
