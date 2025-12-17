"""
Shyam Thakkar's Portfolio Data for RAG System
This file contains structured information about Shyam Thakkar for the chatbot
"""

SHYAM_PORTFOLIO_DATA = [
    # ===== ABOUT ME =====
    {
        "category": "about",
        "title": "Introduction",
        "text": """I'm Shyam Thakkar, a GenAI Developer specializing in building intelligent applications 
        using Large Language Models, LangChain, and LangGraph. I have expertise in AI-driven automation, 
        RAG systems, and integrating LLMs with complex business logic. I'm passionate about creating 
        practical AI solutions that solve real-world problems.""",
        "source": "portfolio"
    },
    {
        "category": "about",
        "title": "Professional Summary",
        "text": """I'm currently working as an SDE-1 (GenAI Developer) at WeServeCodes Pvt Ltd, where I engineer 
        AI-driven automation systems and build robust data-extraction pipelines. I have experience in 
        developing RAG systems, custom tool-call frameworks for LLMs, and dynamic content-generation 
        workflows. My background includes AI/ML internships and data analysis roles.""",
        "source": "resume"
    },
    {
        "category": "about",
        "title": "Contact Information",
        "text": """You can reach me at work.shyamthakkar@gmail.com or call me at +91 9979194059. 
        I'm also active on LinkedIn and GitHub. My portfolio website is at shyam-thakkar.github.io.""",
        "source": "resume"
    },
    
    # ===== EDUCATION =====
    {
        "category": "education",
        "title": "Bachelor's Degree - Computer Engineering",
        "text": """I completed my Bachelor's degree in Computer Engineering from G H Patel College of 
        Engineering and Technology (GCET) in Anand, India, from 2021 to 2025. I graduated with 
        a CGPA of 8.73, demonstrating strong academic performance throughout my undergraduate studies.""",
        "source": "resume"
    },
    
    # ===== TECHNICAL SKILLS =====
    {
        "category": "skills",
        "title": "Programming Languages",
        "text": """I am proficient in multiple programming languages including Python (my primary language), 
        JavaScript, C++, C, and Java. I use Python extensively for AI/ML development, backend systems, 
        and automation. JavaScript for web development, and C++/Java for systems programming and 
        algorithmic problem-solving.""",
        "source": "resume"
    },
    {
        "category": "skills",
        "title": "AI/ML Frameworks and Libraries",
        "text": """I have extensive experience with AI/ML frameworks including Django, LangChain, LangGraph, 
        TensorFlow, Keras, PyTorch, and OpenCV. I specialize in LangChain and LangGraph for building 
        LLM applications and RAG systems. I use TensorFlow, Keras, and PyTorch for deep learning models, 
        and OpenCV for computer vision applications.""",
        "source": "resume"
    },
    {
        "category": "skills",
        "title": "Web Development and Automation",
        "text": """I work with web frameworks like Django and FastAPI for building backend systems and APIs. 
        For frontend development and data apps, I use Streamlit. I'm experienced with web automation 
        using Selenium and Playwright for scraping, testing, and automated workflows.""",
        "source": "resume"
    },
    {
        "category": "skills",
        "title": "Tools and Technologies",
        "text": """My technical toolkit includes Git for version control, Docker for containerization, 
        Vector Databases (like Weaviate, pgvector) for RAG systems, SQL for database management, 
        and various tools for RAG Systems development, Prompt Engineering, LLM Evaluation, OCR, 
        Data Cleaning, Preprocessing, and Visualization. I also build and consume RESTful APIs.""",
        "source": "resume"
    },
    {
        "category": "skills",
        "title": "GenAI and LLM Expertise",
        "text": """I specialize in Generative AI and Large Language Models. My expertise includes building 
        RAG (Retrieval-Augmented Generation) systems, prompt engineering, LLM evaluation, custom 
        tool-call frameworks, and integrating LLMs with business logic. I work with various LLM 
        models including LLaMA 3, DeepSeek R1, and commercial APIs.""",
        "source": "resume"
    },
    
    # ===== WORK EXPERIENCE =====
    {
        "category": "experience",
        "title": "WeServeCodes Pvt Ltd - SDE-1 (GenAI Developer)",
        "text": """I'm currently working as an SDE-1 (GenAI Developer) at WeServeCodes Pvt Ltd since June 2025. 
        In this role, I engineer AI-driven automation systems by integrating LLMs with complex business 
        logic, enabling natural-language instructions to trigger reliable, validated actions across 
        internal platforms. I build robust data-extraction and validation pipelines that combine web 
        automation, structured LLM output, and real-time API checks to ensure accuracy, consistency, 
        and trust in generated data. I design and implement custom tool-call frameworks allowing LLMs 
        to safely interact with external APIs, verify user-provided inputs, and request missing or 
        corrected information when required. I also develop dynamic content-generation workflows powered 
        by rule-based logic and LLM capabilities, improving data quality, operational efficiency, and 
        automation across business processes.""",
        "source": "resume"
    },
    {
        "category": "experience",
        "title": "CrossShores Infotech - AI/ML Intern",
        "text": """I worked as an AI/ML Intern at CrossShores Infotech from December 2024 to June 2025. 
        During this internship, I developed an in-house API for background removal, designed for 
        cleaning logos and product images using BiRefNet and open-source Rembg, eliminating the need 
        for third-party services and reducing client costs by 7%. I designed and implemented a 
        Candidate Filtering RAG System using LLM-based prompt engineering, hybrid retrievers, and 
        CrossEncoder rerankers, enabling accurate matching of resumes to job descriptions through an 
        ensemble of SelfQueryRetriever, ideal JD generation using LLaMA 3, and key detail extraction 
        using DeepSeek R1. I built a modular pipeline incorporating question generation, JSON-based 
        metadata filtering, and vector store retrieval using Weaviate to optimize relevance scoring 
        and document reranking.""",
        "source": "resume"
    },
    {
        "category": "experience",
        "title": "Tech Elecon Pvt. Ltd. - Data Analyst Intern",
        "text": """I worked as a Data Analyst Intern at Tech Elecon Pvt. Ltd. from May 2024 to June 2024. 
        In this role, I developed an invoice reader project using optical character recognition (OCR) 
        technology to accurately read and display the contents of invoices. I also led a team of interns 
        on various projects, providing guidance and support to ensure successful project completion. 
        This experience helped me develop leadership skills and practical experience with OCR technology.""",
        "source": "resume"
    },
    
    # ===== PROJECTS =====
    {
        "category": "projects",
        "title": "Karate Kata Evaluation System",
        "text": """I designed and developed a Karate Kata Evaluation System using Google MoveNet and a custom 
        deep neural network for real-time pose detection and analysis. The system integrates TensorFlow, 
        OpenCV, Scikit-Learn, and Keras for posture assessment and movement analysis. I built and hosted 
        a user-friendly Streamlit interface for real-time feedback and performance evaluation, ensuring 
        accuracy through rigorous testing and optimization. The project demonstrates my expertise in 
        computer vision, deep learning, and building practical AI applications. You can try the live 
        demo at karatekataevaluation.streamlit.app and view the code on my GitHub.""",
        "source": "resume"
    },
    {
        "category": "projects",
        "title": "Stock Price Prediction System",
        "text": """I developed a real-time stock price prediction web application using Streamlit and LSTM 
        models for accurate 7-day forecasts, integrating real-time data sources. The project implements 
        data preprocessing and visualization with Pandas and NumPy to enhance user experience. I built 
        and trained an LSTM model using TensorFlow and Keras, employing a sliding window algorithm for 
        improved accuracy. This project showcases my skills in time series analysis, deep learning, 
        and building interactive data applications.""",
        "source": "resume"
    },
    {
        "category": "projects",
        "title": "Candidate Filtering RAG System",
        "text": """At CrossShores Infotech, I designed and implemented a sophisticated Candidate Filtering 
        RAG System that uses LLM-based prompt engineering, hybrid retrievers, and CrossEncoder rerankers 
        to match resumes with job descriptions accurately. The system uses an ensemble approach combining 
        SelfQueryRetriever, ideal job description generation with LLaMA 3, and key detail extraction 
        using DeepSeek R1. I built a modular pipeline with question generation, JSON-based metadata 
        filtering, and vector store retrieval using Weaviate for optimized relevance scoring and 
        document reranking. This project demonstrates my expertise in building production-ready RAG 
        systems.""",
        "source": "resume"
    },
    {
        "category": "projects",
        "title": "Background Removal API",
        "text": """I developed an in-house API for background removal at CrossShores Infotech, designed 
        specifically for cleaning logos and product images. The API uses BiRefNet and open-source 
        Rembg models, eliminating the need for expensive third-party services and reducing client 
        costs by 7%. This project showcases my ability to build cost-effective AI solutions that 
        provide real business value.""",
        "source": "resume"
    },
    {
        "category": "projects",
        "title": "Invoice Reader OCR System",
        "text": """At Tech Elecon Pvt. Ltd., I developed an invoice reader project using optical character 
        recognition (OCR) technology to accurately read and display the contents of invoices. The 
        system automates the extraction of key information from invoices, improving efficiency and 
        reducing manual data entry errors. This project demonstrates my practical experience with 
        OCR technology and document processing.""",
        "source": "resume"
    },
    {
        "category": "projects",
        "title": "Portfolio RAG Chatbot",
        "text": """I built an intelligent chatbot for my portfolio website using RAG (Retrieval-Augmented 
        Generation) technology. The system uses Django Channels for WebSocket connections, PostgreSQL 
        with pgvector for vector storage, LangChain for RAG orchestration, and OpenAI embeddings and 
        GPT models for generating responses. The chatbot features session management, allowing users 
        to have continuous conversations, and can answer questions about my experience, skills, and 
        projects based on semantic search through my portfolio data. This project showcases my 
        full-stack development skills and expertise in building production-ready RAG systems.""",
        "source": "portfolio"
    },
    
    # ===== ACHIEVEMENTS & HIGHLIGHTS =====
    {
        "category": "achievements",
        "title": "Cost Reduction Achievement",
        "text": """At CrossShores Infotech, I successfully reduced client costs by 7% by developing an 
        in-house background removal API that eliminated the need for expensive third-party services. 
        This demonstrates my ability to create cost-effective solutions that provide tangible business value.""",
        "source": "resume"
    },
    {
        "category": "achievements",
        "title": "Academic Excellence",
        "text": """I graduated with a CGPA of 8.73 from G H Patel College of Engineering and Technology, 
        demonstrating consistent academic excellence throughout my Bachelor's degree in Computer Engineering.""",
        "source": "resume"
    },
    {
        "category": "achievements",
        "title": "Leadership Experience",
        "text": """During my internship at Tech Elecon Pvt. Ltd., I led a team of interns on various projects, 
        providing guidance and support to ensure successful project completion. This experience developed 
        my leadership and mentoring skills.""",
        "source": "resume"
    },
    
    # ===== INTERESTS & SPECIALIZATIONS =====
    {
        "category": "interests",
        "title": "Areas of Expertise",
        "text": """My primary areas of expertise include Generative AI, Large Language Models (LLMs), 
        RAG (Retrieval-Augmented Generation) systems, AI automation, prompt engineering, and building 
        intelligent applications. I specialize in integrating LLMs with business logic, creating custom 
        tool-call frameworks, and developing data-extraction pipelines. I'm also experienced in computer 
        vision, deep learning, and building web applications.""",
        "source": "portfolio"
    },
    {
        "category": "interests",
        "title": "Technology Focus",
        "text": """I focus on cutting-edge AI technologies including LangChain, LangGraph, vector databases, 
        and various LLM models. I'm passionate about building practical AI solutions that solve real-world 
        problems, particularly in automation, data extraction, and intelligent content generation. I stay 
        updated with the latest developments in GenAI and continuously experiment with new tools and 
        techniques.""",
        "source": "portfolio"
    },
]
