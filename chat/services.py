"""
RAG Service for Multi-Tenant Portfolio Chatbot
All queries MUST be scoped to user_id for isolation
"""
import os
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
from pathlib import Path

# Ensure environment variables are loaded
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

from django.conf import settings
from django.contrib.auth import get_user_model

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document as LangChainDocument

from .models import RAGDocument

logger = logging.getLogger(__name__)
User = get_user_model()


class RAGService:
    """
    Multi-tenant RAG service with strict user isolation.
    All operations are scoped to a specific user_id.
    """
    
    def __init__(self, user_id: int, owner_name: str = None):
        """
        Initialize RAG service for a specific user.
        
        Args:
            user_id: The user ID to scope all operations to
            owner_name: Name of the portfolio owner for personalized responses
        """
        self.user_id = user_id
        self.owner_name = owner_name or self._get_owner_name(user_id)
        self.google_api_key = os.getenv('GOOGLE_API_KEY')
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        # Lazy-loaded instances
        self._embeddings = None
        self._llm = None
    
    def _get_owner_name(self, user_id: int) -> str:
        """Get owner name from user model"""
        try:
            user = User.objects.get(id=user_id)
            return user.name or user.email.split('@')[0]
        except:
            return "the portfolio owner"
    
    @property
    def embeddings(self):
        """Lazy load Google embeddings (768 dimensions)"""
        if self._embeddings is None:
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model="models/text-embedding-004",
                google_api_key=self.google_api_key
            )
        return self._embeddings
    
    @property
    def llm(self):
        """Lazy load Groq LLM"""
        if self._llm is None:
            self._llm = ChatGroq(
                model="llama-3.1-8b-instant",
                temperature=0.3,  # Lower temperature for factual responses
                groq_api_key=self.groq_api_key
            )
        return self._llm
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embeddings.embed_query(text)
    
    def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        section: Optional[str] = None,
        portfolio_version: Optional[str] = None
    ) -> List[RAGDocument]:
        """
        Perform similarity search ALWAYS filtered by user_id.
        
        Args:
            query: Search query
            top_k: Number of results
            section: Optional section filter
            portfolio_version: Optional version filter
            
        Returns:
            List of RAGDocument objects
        """
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Build base queryset - ALWAYS filtered by user_id
        queryset = RAGDocument.objects.filter(user_id=self.user_id)
        
        # Apply optional filters
        if section:
            queryset = queryset.filter(section=section)
        if portfolio_version:
            queryset = queryset.filter(portfolio_version=portfolio_version)
        
        # Use pgvector's L2 distance ordering
        # Note: pgvector uses cosine distance with <=> operator
        from pgvector.django import L2Distance
        
        results = queryset.annotate(
            distance=L2Distance('embedding', query_embedding)
        ).order_by('distance')[:top_k]
        
        return list(results)
    
    def get_prompt_template(self) -> PromptTemplate:
        """
        Get the RAG prompt template.
        Friendly, cheerful tone with third person references.
        """
        template = f"""You are a friendly and cheerful AI assistant for {self.owner_name}'s portfolio! 🎉

Your personality:
- Be warm, enthusiastic, and helpful
- Use a conversational and engaging tone
- Add appropriate emojis occasionally to be friendly (but don't overdo it)
- Always refer to {self.owner_name} in third person (e.g., "{self.owner_name} has...", "{self.owner_name} worked on...")

STRICT RULES:
1. Answer ONLY using the provided context below
2. If the answer is NOT in the context, say something like "Hmm, I don't have that specific info about {self.owner_name} yet! 🤔"
3. Do NOT make up or invent any information
4. Do NOT use external knowledge - only what's in the context
5. Keep responses concise but friendly

Context from {self.owner_name}'s portfolio:
{{context}}

Question: {{question}}

Answer:"""
        
        return PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
    
    def process_query(
        self,
        query: str,
        top_k: int = 5,
        section: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user query using RAG pipeline.
        
        Args:
            query: User's question
            top_k: Number of documents to retrieve
            section: Optional section filter
            chat_history: Optional list of previous messages for context
            
        Returns:
            Dictionary with response and metadata
        """
        try:
            # 1. Retrieve relevant documents (user-scoped)
            docs = self.similarity_search(query, top_k=top_k, section=section)
            
            if not docs:
                return {
                    "response": "I don't have any portfolio information available yet. Please try again later.",
                    "sources": [],
                    "success": True,
                    "doc_ids": []
                }
            
            # 2. Build context from retrieved documents
            context_parts = []
            for doc in docs:
                part = f"[{doc.section.upper()}]"
                if doc.title:
                    part += f" {doc.title}:"
                part += f"\n{doc.text}"
                context_parts.append(part)
            
            context = "\n\n".join(context_parts)
            
            # 3. Build prompt
            prompt = self.get_prompt_template()
            formatted_prompt = prompt.format(context=context, question=query)
            
            # 4. Add chat history context if provided (last 3 only)
            if chat_history:
                history_context = "\n\nPrevious conversation:\n"
                for msg in chat_history[-3:]:  # Last 3 messages only
                    role = "User" if msg.get('role') == 'user' else "Assistant"
                    history_context += f"{role}: {msg.get('content', '')[:150]}\n"
                formatted_prompt = history_context + "\n" + formatted_prompt
            
            # 5. Generate response
            response = self.llm.invoke(formatted_prompt)
            bot_response = response.content if hasattr(response, 'content') else str(response)
            
            # 6. Format sources
            sources = [
                {
                    "id": doc.id,
                    "section": doc.section,
                    "title": doc.title,
                    "snippet": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
                }
                for doc in docs
            ]
            
            return {
                "response": bot_response,
                "sources": sources,
                "success": True,
                "doc_ids": [doc.id for doc in docs]
            }
            
        except Exception as e:
            logger.error(f"Error processing query for user {self.user_id}: {e}", exc_info=True)
            return {
                "response": "I'm having trouble processing your question. Please try again.",
                "sources": [],
                "success": False,
                "error": str(e),
                "doc_ids": []
            }


class RAGDocumentGenerator:
    """
    Generates RAG documents from portfolio data.
    Used to rebuild embeddings when portfolio changes.
    """
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.rag_service = RAGService(user_id)
    
    def rebuild(self, portfolio_version: str = "") -> int:
        """
        Rebuild all RAG documents for a user from their portfolio.
        
        Args:
            portfolio_version: Version string for the documents
            
        Returns:
            Number of documents created
        """
        from profiles.models import Portfolio, PortfolioProfile, PortfolioExperience, PortfolioProject, PortfolioEducation, PortfolioTech
        
        # Delete old documents
        RAGDocument.objects.filter(user_id=self.user_id).delete()
        
        try:
            user = User.objects.get(id=self.user_id)
            portfolio = user.portfolios.first()
            
            if not portfolio:
                logger.warning(f"No portfolio found for user {self.user_id}")
                return 0
            
        except User.DoesNotExist:
            logger.error(f"User {self.user_id} not found")
            return 0
        
        documents_created = 0
        
        # 1. Bio/Profile
        try:
            profile = portfolio.profile
            if profile.headline or profile.short_bio or profile.long_bio:
                bio_text = f"{profile.headline}\n\n{profile.short_bio}\n\n{profile.long_bio}".strip()
                if bio_text:
                    self._create_document(
                        title="About Me",
                        text=bio_text,
                        section="bio",
                        portfolio_version=portfolio_version
                    )
                    documents_created += 1
        except Exception as e:
            logger.debug(f"No profile for user {self.user_id}: {e}")
        
        # 2. Work Experience
        for exp in portfolio.experiences.all():
            text = f"Role: {exp.role}\nCompany: {exp.company_name}\n"
            if exp.start_date:
                text += f"Period: {exp.start_date}"
                if exp.end_date:
                    text += f" to {exp.end_date}"
                elif exp.is_current:
                    text += " to Present"
                text += "\n"
            if exp.description:
                text += f"Description: {exp.description}"
            
            self._create_document(
                title=f"{exp.role} at {exp.company_name}",
                text=text,
                section="experience",
                portfolio_version=portfolio_version
            )
            documents_created += 1
        
        # 3. Projects
        for project in portfolio.projects.all():
            text = f"Project: {project.title}\n"
            if project.description:
                text += f"Description: {project.description}\n"
            if project.key_features:
                text += f"Key Features: {', '.join(project.key_features)}\n"
            if project.technical_challenges:
                text += f"Technical Challenges: {', '.join(project.technical_challenges)}\n"
            if project.repo_url:
                text += f"Repository: {project.repo_url}\n"
            if project.live_url:
                text += f"Live URL: {project.live_url}\n"
            
            # Get tech used
            tech_names = [t.display_name for t in project.tech_used.all()]
            if tech_names:
                text += f"Technologies: {', '.join(tech_names)}"
            
            self._create_document(
                title=project.title,
                text=text,
                section="projects",
                portfolio_version=portfolio_version
            )
            documents_created += 1
        
        # 4. Education
        for edu in portfolio.education.all():
            text = f"Degree: {edu.degree}\n"
            text += f"Institution: {edu.institution}\n"
            if edu.field_of_study:
                text += f"Field: {edu.field_of_study}\n"
            if edu.grade:
                text += f"Grade: {edu.grade}"
                if edu.grade_type:
                    text += f" ({edu.grade_type.upper()})"
                text += "\n"
            if edu.start_date:
                text += f"Period: {edu.start_date}"
                if edu.end_date:
                    text += f" to {edu.end_date}"
                text += "\n"
            if edu.description:
                text += f"Description: {edu.description}"
            
            self._create_document(
                title=f"{edu.degree} at {edu.institution}",
                text=text,
                section="education",
                portfolio_version=portfolio_version
            )
            documents_created += 1
        
        # 5. Skills/Tech Stack
        tech_stack = portfolio.tech_stack.all().select_related('tech')
        if tech_stack:
            skills_text = "Technical Skills:\n"
            for pt in tech_stack:
                line = f"- {pt.tech.display_name}"
                if pt.proficiency:
                    line += f" ({pt.proficiency})"
                skills_text += line + "\n"
            
            self._create_document(
                title="Technical Skills",
                text=skills_text,
                section="skills",
                portfolio_version=portfolio_version
            )
            documents_created += 1
        
        logger.info(f"Created {documents_created} RAG documents for user {self.user_id}")
        return documents_created
    
    def _create_document(
        self,
        title: str,
        text: str,
        section: str,
        portfolio_version: str
    ) -> RAGDocument:
        """Create a single RAG document with embedding"""
        embedding = self.rag_service.embed_text(text)
        
        return RAGDocument.objects.create(
            user_id=self.user_id,
            title=title,
            text=text,
            section=section,
            embedding=embedding,
            portfolio_version=portfolio_version
        )
