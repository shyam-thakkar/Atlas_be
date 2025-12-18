import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from profiles.models import SocialRegistry
from profiles.utils import download_and_process_icon

COMMON_SOCIALS = [
    ("GitHub", "github", "https://cdn.simpleicons.org/github", "https://github.com/"),
    ("LinkedIn", "linkedin", "https://cdn.simpleicons.org/linkedin", "https://linkedin.com/in/"),
    ("Twitter", "twitter", "https://cdn.simpleicons.org/x", "https://twitter.com/"),
    ("Instagram", "instagram", "https://cdn.simpleicons.org/instagram", "https://instagram.com/"),
    ("Facebook", "facebook", "https://cdn.simpleicons.org/facebook", "https://facebook.com/"),
    ("YouTube", "youtube", "https://cdn.simpleicons.org/youtube", "https://youtube.com/@"),
    ("TikTok", "tiktok", "https://cdn.simpleicons.org/tiktok", "https://tiktok.com/@"),
    ("Medium", "medium", "https://cdn.simpleicons.org/medium", "https://medium.com/@"),
    ("Dev.to", "devto", "https://cdn.simpleicons.org/devdotto", "https://dev.to/"),
    ("Stack Overflow", "stackoverflow", "https://cdn.simpleicons.org/stackoverflow", "https://stackoverflow.com/users/"),
    ("Dribbble", "dribbble", "https://cdn.simpleicons.org/dribbble", "https://dribbble.com/"),
    ("Behance", "behance", "https://cdn.simpleicons.org/behance", "https://behance.net/"),
    ("Portfolio", "portfolio", "https://cdn.simpleicons.org/internetarchive", None),
    ("Email", "email", "https://cdn.simpleicons.org/gmail", "mailto:"),
]

def populate_socials():
    print("🚀 Starting Social Registry Seeding...\n")
    
    for display_name, code_name, icon_url, base_url in COMMON_SOCIALS:
        if SocialRegistry.objects.filter(code_name=code_name).exists():
            print(f"  ⏭ Skipping {display_name}")
            continue
        
        print(f"  🔧 Processing {display_name}...")
        content_file, icon_type = download_and_process_icon(icon_url, code_name)
        
        if not content_file:
            print(f"  ❌ Failed icon download: {icon_url}")
            continue
        
        social = SocialRegistry(
            display_name=display_name,
            code_name=code_name,
            icon_type=icon_type,
            icon_source_url=icon_url,
            base_url=base_url,
            is_verified=True,
        )
        
        social.icon_path.save(content_file.name, content_file, save=True)
        print(f"  ✅ Added {display_name}")
    
    print(f"\n✨ Seeding complete! Total socials: {SocialRegistry.objects.count()}")

if __name__ == "__main__":
    populate_socials()
