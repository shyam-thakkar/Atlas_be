from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field, ConfigDict, field_validator, model_validator

class Hero(BaseModel):
    full_name: str = Field(description="Full name of the developer")
    headline: str = Field(description="Professional headline (e.g. 'Software Engineer'). Generate a strong one if missing.")
    short_bio: str = Field(description="Short biography (max 200 chars). Generate an engaging summary of skills/role if missing.")
    profile_image: Optional[str] = Field(default=None, description="URL to profile photo")

class Socials(BaseModel):
    model_config = ConfigDict(extra='allow')  # Allow any additional social platforms
    
    github: str = Field(default="", description="GitHub profile URL or empty string")
    linkedin: str = Field(default="", description="LinkedIn profile URL or empty string")
    twitter: str = Field(default="", description="Twitter profile URL or empty string")
    portfolio: str = Field(default="", description="Personal portfolio URL or empty string")

    @field_validator('github', 'linkedin', 'twitter', 'portfolio')
    @classmethod
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
             raise ValueError('Must be a valid URL starting with http:// or https://')
        return v
    
    @model_validator(mode='after')
    def validate_extra_socials(self):
        # Validate any extra social links as well
        if hasattr(self, '__pydantic_extra__') and self.__pydantic_extra__:
            for key, value in self.__pydantic_extra__.items():
                if value and isinstance(value, str):
                    # Allow email addresses (plain or mailto:)
                    if key.lower() == 'email':
                        # Email can be plain email or mailto:
                        if not (value.startswith('mailto:') or '@' in value):
                            raise ValueError(f'{key}: Must be a valid email address or mailto: link')
                    # All other socials must be URLs
                    elif not (value.startswith('http://') or value.startswith('https://')):
                        raise ValueError(f'{key}: Must be a valid URL starting with http:// or https://')
        return self

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
    key_features: Optional[List[str]] = Field(default_factory=list, description="List of key features (bullet points)")
    technical_challenges: Optional[List[str]] = Field(default_factory=list, description="List of technical challenges faced")
    year: Optional[str] = Field(default="", description="Year of project completion (e.g., '2024')")
    project_type: Optional[str] = Field(default="", description="Type of project (e.g., 'Solo Project', 'Team Project')")

    @field_validator('github_link', 'live_link')
    @classmethod
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
             raise ValueError('Must be a valid URL starting with http:// or https://')
        return v

class About(BaseModel):
    long_bio: str = Field(description="Detailed professional biography. Generate a comprehensive narrative of the candidate's journey and expertise based on the resume.")

class Education(BaseModel):
    institution: str = Field(description="Name of the educational institution (e.g., 'MIT', 'Stanford University')")
    degree: str = Field(description="Degree obtained (e.g., 'Bachelor of Technology', 'Master of Science')")
    field_of_study: str = Field(default="", description="Field/major (e.g., 'Computer Science', 'Electrical Engineering')")
    grade: str = Field(default="", description="Grade obtained (e.g., '8.5', '85%', '3.8'). Extract EXACT value from resume.")
    grade_type: str = Field(default="", description="Type of grading: 'cgpa', 'sgpa', 'percentage', 'gpa', or 'other'. Infer from grade format.")
    start_year: str = Field(default="", description="Start year (e.g., '2018')")
    end_year: str = Field(default="", description="End year or 'Present' (e.g., '2022')")
    description: str = Field(default="", description="Additional details like honors, relevant coursework, activities")

class PortfolioSchema(BaseModel):
    model_config = ConfigDict(extra='forbid')
    hero: Hero
    socials: Optional[Socials] = Field(default_factory=Socials)
    tech_stack: List[str] = Field(description="List of technical skills")
    experience: List[Experience]
    projects: List[Project]
    education: List[Education] = Field(default_factory=list, description="List of educational qualifications")
    about: About
