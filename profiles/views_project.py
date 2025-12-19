from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import PortfolioProject, Portfolio

class ProjectThumbnailUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Upload a project thumbnail image.
        Expects: project_title (string) and thumbnail (file)
        """
        project_title = request.data.get('project_title')
        thumbnail_file = request.FILES.get('thumbnail')
        
        if not project_title:
            return Response(
                {"error": "project_title is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not thumbnail_file:
            return Response(
                {"error": "thumbnail file is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's portfolio
        try:
            portfolio = Portfolio.objects.get(user=request.user)
        except Portfolio.DoesNotExist:
            return Response(
                {"error": "Portfolio not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Find project by title (case-insensitive)
        project = PortfolioProject.objects.filter(
            portfolio=portfolio,
            title__iexact=project_title
        ).first()
        
        if not project:
            return Response(
                {"error": f"Project '{project_title}' not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Save the thumbnail
        project.thumbnail = thumbnail_file
        project.save()
        
        # Return the thumbnail URL
        from .utils import get_absolute_media_url
        thumbnail_url = get_absolute_media_url(project.thumbnail)
        
        return Response({
            "thumbnail_url": thumbnail_url
        }, status=status.HTTP_200_OK)
