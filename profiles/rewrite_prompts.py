"""
Section-specific prompts for AI rewriting of portfolio descriptions.
Each prompt template uses context from the user's AI snapshot.
"""

# Valid section types
VALID_SECTIONS = [
    'bio_short',
    'bio_long', 
    'headline',
    'experience',
    'project',
    'project_features',
    'project_challenges',
    'education'
]

# ============================================================
# PROFILE/BIO PROMPTS
# ============================================================

BIO_SHORT_PROMPT = """You are improving a short bio for a developer portfolio.

TASK: Rewrite this into a SINGLE, punchy sentence.

CONTEXT:
- Name: {full_name}
- Headline: {headline}
- Tech Stack: {tech_stack}

ORIGINAL:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. MUST be a SINGLE line (under 150 chars preferred)
2. Format ALL tech names like {{{{tech}}}}, e.g. {{{{python}}}}
3. No fluff, just role and key value
4. Use lowercase for tech names inside braces

OUTPUT: Write ONLY the single sentence short bio. No explanations."""

BIO_LONG_PROMPT = """You are improving a long bio for a portfolio.

TASK: Rewrite this into a concise, professional summary focused on skills and expertise.

CONTEXT:
- Name: {full_name}
- Headline: {headline}
- Tech Stack: {tech_stack}
- Experience: {experience_summary}

ORIGINAL:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. Follow this style: "Highly skilled [Role] with expertise in [Areas]. Proficient in languages such as {{{{python}}}}, {{{{javascript}}}}... Experienced in {{{{django}}}}..."
2. Format ALL tech names like {{{{tech}}}}, e.g. {{{{python}}}} (lowercase inside)
3. Keep it to 3-4 sentences maximum
4. Focus heavily on technical skills
5. NEVER invent skills not in the context

OUTPUT: Write ONLY the improved bio paragraph. No explanations."""

HEADLINE_PROMPT = """You are a copywriter improving a professional headline.

TASK: Polish this headline while staying TRUE to the original intent.

CONTEXT:
- Full Name: {full_name}
- Current Headline: {headline}
- Primary Technologies: {primary_tech}
- Most Recent Role: {recent_role}

ORIGINAL HEADLINE TO REWRITE:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. Keep it concise (5-10 words max)
2. Stay TRUE to the original role/identity
3. NEVER add titles or specializations not implied in original
4. Make it impactful but authentic

OUTPUT: Write ONLY the improved headline. No explanations."""

# ============================================================
# EXPERIENCE PROMPTS
# ============================================================

EXPERIENCE_PROMPT = """You are an expert resume writer helping polish a job description.

TASK: Improve the writing quality of this job description while staying TRUE to the original content.

CONTEXT:
- Role: {role}
- Company: {company}
- Duration: {start_date} - {end_date}
- Candidate's Relevant Skills: {tech_stack}

ORIGINAL DESCRIPTION TO REWRITE:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES - FOLLOW STRICTLY:
1. ONLY mention technologies/tools that appear in the ORIGINAL DESCRIPTION or the Context skills
2. NEVER invent metrics, percentages, or numbers that aren't in the original
3. NEVER add technologies that weren't mentioned (like Java, C++, Keras if not in original)
4. Focus on improving CLARITY and IMPACT of what's already written
5. Use action verbs to make existing content more compelling
6. Keep the same scope and meaning as the original
7. If the original lacks specifics, keep it general - don't fabricate details

OUTPUT: Write ONLY the improved description. No explanations."""

# ============================================================
# PROJECT PROMPTS
# ============================================================

PROJECT_PROMPT = """You are a technical writer improving a project description.

TASK: Polish this project description while staying TRUE to the original content.

CONTEXT:
- Project Name: {project_name}
- Technologies Used: {technologies}
- Key Features: {key_features}
- Technical Challenges: {technical_challenges}
- Has Live Demo: {has_live}
- Has GitHub Repo: {has_github}
- Project Type: {project_type}

ORIGINAL DESCRIPTION TO REWRITE:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES - FOLLOW STRICTLY:
1. ONLY mention technologies that appear in the ORIGINAL DESCRIPTION or Context
2. NEVER invent features, metrics, or capabilities not in the original
3. Focus on improving CLARITY and making the existing content more compelling
4. Keep the same scope - don't expand or add claims
5. Make it sound professional but authentic
6. Keep it to 2-4 sentences

OUTPUT: Write ONLY the improved description. No explanations."""

PROJECT_FEATURES_PROMPT = """You are improving project key features for a portfolio.

TASK: Make these features clearer and more impactful while keeping them CONCISE.

CONTEXT:
- Project Name: {project_name}
- Technologies Used: {technologies}

ORIGINAL KEY FEATURES:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. Keep the SAME NUMBER of features
2. Keep each feature SHORT (under 15 words ideally)
3. Stay TRUE to the original meaning - just improve clarity
4. AVOID corporate jargon and buzzwords
5. Be specific and concrete, not vague
6. Start with action verbs when possible

BAD: "Enhancing Predictive Accuracy through Optimized Sliding Window Algorithm Implementation"
GOOD: "Sliding window algorithm for accurate stock predictions"

OUTPUT: Return a JSON array. Example: ["Feature 1", "Feature 2"]
Just the JSON array, no explanations."""

PROJECT_CHALLENGES_PROMPT = """You are improving project technical challenges for a portfolio.

TASK: Make these challenges clearer and more impactful while keeping them CONCISE.

CONTEXT:
- Project Name: {project_name}
- Technologies Used: {technologies}

ORIGINAL TECHNICAL CHALLENGES:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. Keep the SAME NUMBER of challenges
2. Keep each challenge SHORT (under 15 words ideally)
3. Stay TRUE to the original meaning - just improve clarity
4. AVOID corporate jargon and buzzwords
5. Be specific about the technical problem
6. Focus on what was difficult, not the solution

BAD: "Delivering Seamless User Experience with Real-Time Data Integration and Streaming"
GOOD: "Handling real-time data streams without UI lag"

OUTPUT: Return a JSON array. Example: ["Challenge 1", "Challenge 2"]
Just the JSON array, no explanations."""

# ============================================================
# EDUCATION PROMPTS
# ============================================================

EDUCATION_PROMPT = """You are a resume writer improving an education description.

TASK: Polish this education description while staying TRUE to the original content.

CONTEXT:
- Institution: {institution}
- Degree: {degree}
- Field of Study: {field_of_study}
- Grade: {grade} ({grade_type})
- Duration: {start_year} - {end_year}

ORIGINAL DESCRIPTION TO REWRITE:
{content}

USER'S INSTRUCTION:
{user_instruction}

⚠️ CRITICAL RULES:
1. Stay TRUE to the original - improve wording only
2. NEVER add coursework, honors, or achievements not in the original
3. Keep the same meaning and scope
4. Make it professional but authentic

OUTPUT: Write ONLY the improved description. No explanations."""

# ============================================================
# PROMPT GETTER
# ============================================================

def get_prompt_template(section: str) -> str:
    """Get the appropriate prompt template for a section."""
    prompts = {
        'bio_short': BIO_SHORT_PROMPT,
        'bio_long': BIO_LONG_PROMPT,
        'headline': HEADLINE_PROMPT,
        'experience': EXPERIENCE_PROMPT,
        'project': PROJECT_PROMPT,
        'project_features': PROJECT_FEATURES_PROMPT,
        'project_challenges': PROJECT_CHALLENGES_PROMPT,
        'education': EDUCATION_PROMPT,
    }
    return prompts.get(section)
