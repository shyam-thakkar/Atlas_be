from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, field_validator

class Hero(BaseModel):
    full_name: str = Field(description="Full name of the developer")
    headline: str = Field(description="Professional headline (e.g. 'Software Engineer'). Generate a strong one if missing.")
    short_bio: str = Field(description="Short biography (max 200 chars). Generate an engaging summary of skills/role if missing.")

class Socials(BaseModel):
    github: str = Field(description="GitHub profile URL or empty string")
    linkedin: str = Field(description="LinkedIn profile URL or empty string")
    twitter: str = Field(description="Twitter profile URL or empty string")
    portfolio: str = Field(description="Personal portfolio URL or empty string")

    @field_validator('github', 'linkedin', 'twitter', 'portfolio')
    @classmethod
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
             raise ValueError('Must be a valid URL starting with http:// or https://')
        return v

class Experience(BaseModel):
    company: str = Field(description="Company name")
    role: str = Field(description="Job title")
    start_date: str = Field(description="Start date (e.g. 'Jan 2020') or empty")
    end_date: str = Field(description="End date (e.g. 'Present') or empty")
    summary: str = Field(description="Detailed summary of responsibilities and impact. Generate a professional description based on the resume points. Single string.")

class Project(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="Project description. Generate a compelling overview if brief. Single string.")
    technologies: List[str] = Field(description="List of technologies used")
    github_link: str = Field(description="GitHub repository URL or empty")
    live_link: str = Field(description="Live project URL or empty")

    @field_validator('github_link', 'live_link')
    @classmethod
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
             raise ValueError('Must be a valid URL starting with http:// or https://')
        return v

class About(BaseModel):
    long_bio: str = Field(description="Detailed professional biography. Generate a comprehensive narrative of the candidate's journey and expertise based on the resume.")

class PortfolioSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hero: Hero
    socials: Socials
    tech_stack: List[str] = Field(description="List of technical skills")
    experience: List[Experience]
    projects: List[Project]
    about: About
