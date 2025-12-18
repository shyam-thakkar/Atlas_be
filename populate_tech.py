import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from profiles.models import TechRegistry
from profiles.utils import download_and_process_icon
TECH_REGISTRY = {

    # ======================
    # Programming Languages
    # ======================
    "languages": [
        ("Python", "python", "https://cdn.simpleicons.org/python", "https://www.python.org/"),
        ("JavaScript", "javascript", "https://cdn.simpleicons.org/javascript", "https://developer.mozilla.org/en-US/docs/Web/JavaScript"),
        ("TypeScript", "typescript", "https://cdn.simpleicons.org/typescript", "https://www.typescriptlang.org/"),
        ("Go", "go", "https://cdn.simpleicons.org/go", "https://go.dev/"),
        ("Rust", "rust", "https://cdn.simpleicons.org/rust", "https://www.rust-lang.org/"),
        ("Java", "java", "https://cdn.simpleicons.org/java", "https://www.oracle.com/java/"),
        ("C++", "cpp", "https://cdn.simpleicons.org/cplusplus", "https://isocpp.org/"),
    ],

    # ======================
    # Frontend Frameworks
    # ======================
    "frontend": [
        ("React", "react", "https://cdn.simpleicons.org/react", "https://react.dev/"),
        ("Next.js", "nextjs", "https://cdn.simpleicons.org/nextdotjs", "https://nextjs.org/"),
        ("Vue.js", "vue", "https://cdn.simpleicons.org/vuedotjs", "https://vuejs.org/"),
        ("Svelte", "svelte", "https://cdn.simpleicons.org/svelte", "https://svelte.dev/"),
        ("Tailwind CSS", "tailwindcss", "https://cdn.simpleicons.org/tailwindcss", "https://tailwindcss.com/"),
    ],

    # ======================
    # Backend Frameworks
    # ======================
    "backend": [
        ("Django", "django", "https://cdn.simpleicons.org/django", "https://www.djangoproject.com/"),
        ("FastAPI", "fastapi", "https://cdn.simpleicons.org/fastapi", "https://fastapi.tiangolo.com/"),
        ("Node.js", "nodejs", "https://cdn.simpleicons.org/nodedotjs", "https://nodejs.org/"),
        ("Express", "express", "https://cdn.simpleicons.org/express", "https://expressjs.com/"),
        ("Spring Boot", "springboot", "https://cdn.simpleicons.org/springboot", "https://spring.io/projects/spring-boot"),
    ],

    # ======================
    # Databases
    # ======================
    "databases": [
        ("PostgreSQL", "postgresql", "https://cdn.simpleicons.org/postgresql", "https://www.postgresql.org/"),
        ("MySQL", "mysql", "https://cdn.simpleicons.org/mysql", "https://www.mysql.com/"),
        ("MongoDB", "mongodb", "https://cdn.simpleicons.org/mongodb", "https://www.mongodb.com/"),
        ("Redis", "redis", "https://cdn.simpleicons.org/redis", "https://redis.io/"),
        ("SQLite", "sqlite", "https://cdn.simpleicons.org/sqlite", "https://www.sqlite.org/"),
    ],

    # ======================
    # DevOps & Cloud
    # ======================
    "devops": [
        ("Docker", "docker", "https://cdn.simpleicons.org/docker", "https://www.docker.com/"),
        ("Kubernetes", "kubernetes", "https://cdn.simpleicons.org/kubernetes", "https://kubernetes.io/"),
        ("AWS", "aws", "https://cdn.simpleicons.org/amazonaws", "https://aws.amazon.com/"),
        ("Google Cloud", "gcp", "https://cdn.simpleicons.org/googlecloud", "https://cloud.google.com/"),
        ("Azure", "azure", "https://cdn.simpleicons.org/microsoftazure", "https://azure.microsoft.com/"),
        ("Nginx", "nginx", "https://cdn.simpleicons.org/nginx", "https://nginx.org/"),
    ],

    # ======================
    # AI / ML / GenAI
    # ======================
    "ai_ml": [
        ("LangChain", "langchain", "https://cdn.simpleicons.org/langchain", "https://python.langchain.com/"),
        ("LangGraph", "langgraph", "https://raw.githubusercontent.com/langchain-ai/langgraph/main/docs/static/img/langgraph.svg", "https://langchain-ai.github.io/langgraph/"),
        ("OpenAI", "openai", "https://cdn.simpleicons.org/openai", "https://openai.com/"),
        ("TensorFlow", "tensorflow", "https://cdn.simpleicons.org/tensorflow", "https://www.tensorflow.org/"),
        ("PyTorch", "pytorch", "https://cdn.simpleicons.org/pytorch", "https://pytorch.org/"),
        ("Hugging Face", "huggingface", "https://cdn.simpleicons.org/huggingface", "https://huggingface.co/"),
        ("Pinecone", "pinecone", "https://cdn.simpleicons.org/pinecone", "https://www.pinecone.io/"),
        ("Weaviate", "weaviate", "https://cdn.simpleicons.org/weaviate", "https://weaviate.io/"),
    ],

    # ======================
    # Tools & Platforms
    # ======================
    "tools": [
        ("Git", "git", "https://cdn.simpleicons.org/git", "https://git-scm.com/"),
        ("GitHub", "github", "https://cdn.simpleicons.org/github", "https://github.com/"),
        ("Postman", "postman", "https://cdn.simpleicons.org/postman", "https://www.postman.com/"),
        ("VS Code", "vscode", "https://cdn.simpleicons.org/visualstudiocode", "https://code.visualstudio.com/"),
        ("Linux", "linux", "https://cdn.simpleicons.org/linux", "https://www.linux.org/"),
    ],
}
def populate():
    print("🚀 Starting Tech Registry Seeding...\n")

    for category, techs in TECH_REGISTRY.items():
        print(f"\n📦 Category: {category.upper()}")

        for display_name, code_name, icon_url, doc_url in techs:
            if TechRegistry.objects.filter(code_name=code_name).exists():
                print(f"  ⏭ Skipping {display_name}")
                continue

            print(f"  🔧 Processing {display_name}...")
            content_file, icon_type = download_and_process_icon(icon_url, code_name)

            if not content_file:
                print(f"  ❌ Failed icon download: {icon_url}")
                continue

            tech = TechRegistry(
                display_name=display_name,
                code_name=code_name,
                icon_type=icon_type,
                icon_source_url=icon_url,
                doc_url=doc_url,
                is_verified=True,
            )

            tech.icon_path.save(content_file.name, content_file, save=True)
            print(f"  ✅ Added {display_name}")
if __name__ == "__main__":
    populate()
