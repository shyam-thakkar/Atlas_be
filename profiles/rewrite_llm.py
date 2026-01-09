"""
LLM integration for AI rewriting of portfolio descriptions.
Uses Groq LLM with context from PortfolioAISnapshot.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from .rewrite_prompts import get_prompt_template, VALID_SECTIONS

logger = logging.getLogger(__name__)


# Pydantic schema for list-type outputs (features, challenges)
class RewrittenListSchema(BaseModel):
    """Schema for structured list output from LLM."""
    items: List[str] = Field(description="List of rewritten items")


def get_rewrite_llm():
    """
    Initialize Groq LLM for rewriting tasks.
    Uses slightly higher temperature for creative rewriting.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    
    return ChatGroq(
        temperature=0.3,  # Slightly creative but still controlled
        model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        groq_api_key=api_key
    )


def get_structured_list_llm():
    """
    Initialize Groq LLM with structured output for list responses.
    Returns items as a proper Python list.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    
    llm = ChatGroq(
        temperature=0.3,
        model_name="meta-llama/llama-4-scout-17b-16e-instruct",
        groq_api_key=api_key
    )
    return llm.with_structured_output(RewrittenListSchema)


def build_context_for_bio(context: Dict[str, Any], section: str) -> Dict[str, str]:
    """Build context dict for bio/profile sections."""
    hero = context.get('hero', {})
    tech_stack = context.get('tech_stack', [])
    experiences = context.get('experience', [])
    
    # Build experience summary for long bio
    experience_summary = ""
    for exp in experiences[:3]:  # Top 3 experiences
        experience_summary += f"- {exp.get('role', 'Role')} at {exp.get('company', 'Company')}\n"
    
    return {
        'full_name': hero.get('full_name', 'Professional'),
        'headline': hero.get('headline', ''),
        'tech_stack': ', '.join(tech_stack[:30]) if tech_stack else 'Various technologies',
        'experience_count': str(len(experiences)),
        'experience_summary': experience_summary or 'No experience data available',
        'primary_tech': ', '.join(tech_stack[:10]) if tech_stack else '',
        'recent_role': f"{experiences[0].get('role', '')} at {experiences[0].get('company', '')}" if experiences else ''
    }


def build_context_for_experience(context: Dict[str, Any], item_index: int) -> Dict[str, str]:
    """Build context dict for experience section."""
    experiences = context.get('experience', [])
    tech_stack = context.get('tech_stack', [])
    
    if item_index >= len(experiences):
        # Fallback if index is out of range
        return {
            'role': 'Software Engineer',
            'company': 'Company',
            'start_date': '',
            'end_date': 'Present',
            'tech_stack': ', '.join(tech_stack[:10]) if tech_stack else ''
        }
    
    exp = experiences[item_index]
    return {
        'role': exp.get('role', ''),
        'company': exp.get('company', ''),
        'start_date': exp.get('start_date', ''),
        'end_date': exp.get('end_date', 'Present'),
        'tech_stack': ', '.join(tech_stack[:10]) if tech_stack else ''
    }


def build_context_for_project(context: Dict[str, Any], item_index: int) -> Dict[str, str]:
    """Build context dict for project section."""
    projects = context.get('projects', [])
    
    if item_index >= len(projects):
        return {
            'project_name': 'Project',
            'technologies': '',
            'key_features': '',
            'technical_challenges': '',
            'has_live': 'No',
            'has_github': 'No',
            'project_type': ''
        }
    
    proj = projects[item_index]
    return {
        'project_name': proj.get('name', ''),
        'technologies': ', '.join(proj.get('technologies', [])),
        'key_features': ', '.join(proj.get('key_features', [])[:5]) if proj.get('key_features') else '',
        'technical_challenges': ', '.join(proj.get('technical_challenges', [])[:3]) if proj.get('technical_challenges') else '',
        'has_live': 'Yes' if proj.get('live_link') else 'No',
        'has_github': 'Yes' if proj.get('github_link') else 'No',
        'project_type': proj.get('project_type', '')
    }


def build_context_for_education(context: Dict[str, Any], item_index: int) -> Dict[str, str]:
    """Build context dict for education section."""
    education = context.get('education', [])
    
    if item_index >= len(education):
        return {
            'institution': 'University',
            'degree': 'Degree',
            'field_of_study': '',
            'grade': '',
            'grade_type': '',
            'start_year': '',
            'end_year': ''
        }
    
    edu = education[item_index]
    return {
        'institution': edu.get('institution', ''),
        'degree': edu.get('degree', ''),
        'field_of_study': edu.get('field_of_study', ''),
        'grade': edu.get('grade', ''),
        'grade_type': edu.get('grade_type', ''),
        'start_year': edu.get('start_year', ''),
        'end_year': edu.get('end_year', '')
    }


def rewrite_with_context(
    section: str,
    content: str,
    user_instruction: str,
    context: Dict[str, Any],
    item_index: int = 0
) -> str:
    """
    Rewrite content using LLM with context from AI snapshot.
    
    Args:
        section: Section type (bio_short, bio_long, headline, experience, project, education)
        content: Current content to rewrite
        user_instruction: User's specific instructions
        context: The extracted_jsonb from PortfolioAISnapshot
        item_index: Index for array items (experience, project, education)
    
    Returns:
        Rewritten content string
    """
    if section not in VALID_SECTIONS:
        raise ValueError(f"Invalid section: {section}. Must be one of {VALID_SECTIONS}")
    
    # Get prompt template
    prompt_template = get_prompt_template(section)
    if not prompt_template:
        raise ValueError(f"No prompt template found for section: {section}")
    
    # Build section-specific context
    if section in ['bio_short', 'bio_long', 'headline']:
        section_context = build_context_for_bio(context, section)
    elif section == 'experience':
        section_context = build_context_for_experience(context, item_index)
    elif section in ['project', 'project_features', 'project_challenges']:
        section_context = build_context_for_project(context, item_index)
    elif section == 'education':
        section_context = build_context_for_education(context, item_index)
    else:
        section_context = {}
    
    # Add common fields
    section_context['content'] = content
    section_context['user_instruction'] = user_instruction or "Improve the writing quality and make it more professional"
    
    # Format the prompt
    try:
        formatted_prompt = prompt_template.format(**section_context)
    except KeyError as e:
        logger.error(f"Missing context key: {e}")
        raise ValueError(f"Missing context for prompt: {e}")
    
    # Check if this is a list-type section
    is_list_section = section in ['project_features', 'project_challenges']
    
    # Call LLM (use regular LLM for all, parse JSON for list sections)
    try:
        llm = get_rewrite_llm()
        prompt = ChatPromptTemplate.from_messages([
            ("human", "{prompt}")
        ])
        chain = prompt | llm
        
        result = chain.invoke({"prompt": formatted_prompt})
        
        # Extract text from response
        rewritten = result.content if hasattr(result, 'content') else str(result)
        rewritten = rewritten.strip()
        
        if is_list_section:
            # Parse JSON array from response
            import json
            # Clean up the response - remove markdown code blocks if present
            if rewritten.startswith('```'):
                # Remove markdown code block
                lines = rewritten.split('\n')
                rewritten = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
                rewritten = rewritten.strip()
            
            try:
                parsed_list = json.loads(rewritten)
                if isinstance(parsed_list, list):
                    return parsed_list
                else:
                    logger.warning(f"Expected list but got: {type(parsed_list)}")
                    return [rewritten]
            except json.JSONDecodeError as je:
                logger.warning(f"Failed to parse JSON list: {je}. Returning as single item.")
                return [rewritten]
        else:
            return rewritten
        
    except Exception as e:
        logger.error(f"LLM rewrite failed: {e}")
        raise RuntimeError(f"Failed to rewrite content: {e}")

