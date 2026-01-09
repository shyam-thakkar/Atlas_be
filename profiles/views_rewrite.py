"""
API views for AI rewriting of portfolio descriptions.
"""

import logging
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Portfolio, PortfolioAISnapshot
from .rewrite_llm import rewrite_with_context, VALID_SECTIONS

logger = logging.getLogger(__name__)


class RewriteDescriptionView(APIView):
    """
    API endpoint for AI-powered rewriting of portfolio descriptions.
    
    POST /api/profiles/rewrite/
    
    Request Body:
    {
        "section": "experience",  # One of: bio_short, bio_long, headline, experience, project, education
        "content": "Current description text...",
        "user_instruction": "Make it more professional",  # Optional
        "item_index": 0  # Optional, for array items (experience, project, education)
    }
    
    Response:
    {
        "success": true,
        "original": "Current description text...",
        "rewritten": "Improved AI-generated text..."
    }
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Extract request data
        section = request.data.get('section')
        content = request.data.get('content')
        user_instruction = request.data.get('user_instruction', '')
        item_index = request.data.get('item_index', 0)
        
        # Validate required fields
        if not section:
            return Response(
                {'error': 'Missing required field: section'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not content:
            return Response(
                {'error': 'Missing required field: content'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate section type
        if section not in VALID_SECTIONS:
            return Response(
                {
                    'error': f'Invalid section: {section}',
                    'valid_sections': VALID_SECTIONS
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure item_index is an integer
        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            item_index = 0
        
        # Get user's portfolio
        portfolio = Portfolio.objects.filter(user=request.user).first()
        if not portfolio:
            return Response(
                {'error': 'No portfolio found for user'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get the latest AI snapshot for context
        ai_snapshot = PortfolioAISnapshot.objects.filter(
            portfolio=portfolio
        ).order_by('-created_at').first()
        
        if not ai_snapshot:
            return Response(
                {'error': 'No AI snapshot found. Please upload and process a resume first.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get context from snapshot
        context = ai_snapshot.extracted_jsonb
        if not context:
            return Response(
                {'error': 'AI snapshot has no extracted data'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Perform the rewrite
        try:
            rewritten = rewrite_with_context(
                section=section,
                content=content,
                user_instruction=user_instruction,
                context=context,
                item_index=item_index
            )
            
            return Response({
                'success': True,
                'original': content,
                'rewritten': rewritten,
                'section': section
            })
            
        except ValueError as e:
            logger.warning(f"Rewrite validation error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except RuntimeError as e:
            logger.error(f"Rewrite runtime error: {e}")
            return Response(
                {'error': 'Failed to rewrite content. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Unexpected error during rewrite: {e}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
