profile = {
    'name': 'Caleb Mayaka',
    'initials': 'CM',
    'role': 'Software Engineer & Solution Architect',
    'headline': 'I build clean digital products with Django, JavaScript, and practical AI.',
    'summary': (
        'Caleb Mayaka is a software engineer and technology enthusiast who enjoys exploring all things tech. '
        'His interests span software development, computer hardware, device repair, DIY projects, video editing, '
        'graphic design, and artificial intelligence. He believes in continuous learning and enjoys sharing '
        'knowledge through practical experiences and real-world projects.'
    ),
    'location': 'Nairobi, Kenya',
    'email': 'hello@calebmayaka.com',
    'whatsapp_url': 'https://wa.me/254798934667',
    'availability': 'Available for selected freelance and collaboration work',
    'meta_description': (
        'Portfolio of Caleb Mayaka, a full-stack developer building polished web apps, '
        'Django systems, and modern product experiences.'
    ),
}

nav_items = [
    {'label': 'Home', 'url_name': 'home'},
    {'label': 'Blog', 'url': '/blog/'},
]

social_links = [
    {'label': 'Email', 'url': 'mailto:hello@calebmayaka.com'},
]

stats = [
    {'value': '6+', 'label': 'Featured builds'},
    {'value': '12', 'label': 'Core technologies'},
    {'value': '100%', 'label': 'Editable Django content'},
]

skills = [
    {
        'title': 'Microsoft Dynamics NAV / C/AL',
        'description': 'ERP customization and development on Microsoft Dynamics NAV with C/AL — codeunits, pages, reports, and business logic tuned to finance and operations workflows.',
        'tags': ['Dynamics NAV', 'C/AL', 'ERP', 'Reports'],
    },
    {
        'title': 'Python & Django',
        'description': 'Django apps, API design, authentication flows, data models, admin workflows, and deployment-ready structure.',
        'tags': ['Django', 'Python', 'Auth', 'Deployment'],
    },
    {
        'title': 'Django REST Framework',
        'description': 'Designing and building REST APIs — serializers, viewsets, permissions, and versioned endpoints for web and mobile clients.',
        'tags': ['DRF', 'REST', 'Serializers', 'Auth'],
    },
    {
        'title': 'Virtualization — Proxmox & Citrix',
        'description': 'Provisioning and managing virtual infrastructure with Proxmox and Citrix — VMs, containers, and virtual desktops for reliable, isolated environments.',
        'tags': ['Proxmox', 'Citrix', 'VMs', 'Infrastructure'],
    },
    {
        'title': 'Technical Writing',
        'description': 'Clear documentation, guides, and reference material — turning complex systems into content people can actually follow.',
        'tags': ['Docs', 'Guides', 'Editing'],
    },
]

# Gallery photos — single source of truth for the /gallery/ page and the image
# sitemap. Files live under portfolio/static/portfolio/img/gallery/ as
# <slug>.webp / <slug>.jpg (+ <slug>-thumb.*). All are 1200x1600 portraits.
# Every photo stays in the image sitemap and the gallery's structured data;
# only those with 'visible': True are shown on the /gallery/ page.
gallery_photos = [
    {
        'slug': 'caleb-mayaka-nairobi-01',
        'alt': 'Caleb Mayaka, software engineer, at a park in Nairobi, Kenya',
        'caption': 'Nairobi, Kenya.',
        'width': 1200, 'height': 1600,
        'visible': True,
    },
    {
        'slug': 'caleb-mayaka-data-center',
        'alt': 'Caleb Mayaka, IT professional, working on a laptop in a data center beside a server rack',
        'caption': 'In the data center — servers, networking, and virtualization.',
        'width': 1200, 'height': 1600,
        'visible': False,
    },
    {
        'slug': 'caleb-mayaka-nairobi-02',
        'alt': 'Caleb Mayaka, side-profile portrait at a park in Nairobi, Kenya',
        'caption': 'Nairobi, Kenya.',
        'width': 1200, 'height': 1600,
        'visible': False,
    },
    {
        'slug': 'caleb-mayaka-poolside',
        'alt': 'Caleb Mayaka, portrait by a poolside in Kenya',
        'caption': 'Poolside.',
        'width': 1200, 'height': 1600,
        'visible': False,
    },
    {
        'slug': 'caleb-mayaka-outdoor-portrait',
        'alt': 'Caleb Mayaka, casual outdoor portrait in rural Kenya',
        'caption': 'Rural Kenya.',
        'width': 1200, 'height': 1600,
        'visible': False,
    },
]

tech_stack = [
    'Microsoft Dynamics NAV / C/AL',
    'Python & Django',
    'Django REST Framework',
    'Virtualization — Proxmox & Citrix',
    'Technical Writing',
]

homepage_stack = [
    {'name': 'Languages', 'items': 'Python, Rust, SQL, JavaScript'},
    {'name': 'Backend', 'items': 'Django, Django REST Framework, PostgreSQL'},
    {'name': 'ERP', 'items': 'Microsoft Dynamics NAV, C/AL'},
    {'name': 'Infrastructure', 'items': 'Docker, Linux, Windows Server, Proxmox, Citrix'},
    {'name': 'Cloud', 'items': 'AWS, Azure, Cloudflare'},
    {'name': 'Creative', 'items': 'Photoshop, Premiere Pro, After Effects'},
]

projects = [
    {
        'id': 'client-portal',
        'title': 'Client Portal Starter',
        'category': 'Django SaaS',
        'description': 'A secure dashboard concept for managing users, documents, messages, and project progress in one place.',
        'tags': ['Django', 'Auth', 'Dashboards', 'Responsive UI'],
        'impact': 'Designed to reduce scattered communication and make client work easier to track.',
        'status': 'Concept build',
        'link': '#',
        'repo': '#',
    },
    {
        'id': 'inventory-flow',
        'title': 'Inventory Flow',
        'category': 'Operations Tool',
        'description': 'A stock and order tracking interface with searchable records, alerts, and a clean admin-first workflow.',
        'tags': ['Python', 'CRUD', 'Reports', 'Admin'],
        'impact': 'Built around quick scanning, fewer manual errors, and practical day-to-day operations.',
        'status': 'Prototype',
        'link': '#',
        'repo': '#',
    },
    {
        'id': 'portfolio-system',
        'title': 'Portfolio System',
        'category': 'Personal Brand',
        'description': 'This multi-page Django portfolio, shaped as a modern product site while staying lightweight and editable.',
        'tags': ['Django', 'Templates', 'CSS', 'JavaScript'],
        'impact': 'Creates a strong online presence that can grow into a full project and case-study archive.',
        'status': 'Live starter',
        'link': '/',
        'repo': '#',
    },
    {
        'id': 'ai-helpdesk',
        'title': 'AI Helpdesk Assistant',
        'category': 'AI Workflow',
        'description': 'A support assistant concept that drafts replies, classifies requests, and keeps common answers consistent.',
        'tags': ['AI', 'Automation', 'Knowledge Base', 'APIs'],
        'impact': 'Shows how practical AI can save time without replacing human judgment.',
        'status': 'Concept',
        'link': '#',
        'repo': '#',
    },
    {
        'id': 'booking-engine',
        'title': 'Booking Engine',
        'category': 'Web App',
        'description': 'A scheduling and availability workflow for small teams that need appointment requests and confirmations.',
        'tags': ['Forms', 'Calendar', 'Email', 'Django'],
        'impact': 'Turns manual booking into a smoother, more reliable customer experience.',
        'status': 'Planned',
        'link': '#',
        'repo': '#',
    },
    {
        'id': 'finance-lens',
        'title': 'Finance Lens',
        'category': 'Data Dashboard',
        'description': 'A personal finance dashboard concept with budgets, spending categories, and lightweight analytics.',
        'tags': ['Charts', 'Data', 'UI', 'Insights'],
        'impact': 'Makes money patterns easier to understand through direct, uncluttered visuals.',
        'status': 'Concept',
        'link': '#',
        'repo': '#',
    },
    {
        'id': 'kasneb-revision-guides',
        'title': 'KASNEB Revision Guides',
        'category': 'Education platform',
        'description': 'A digital reading platform for official KASNEB revision guides, with student sign-in and access to guides purchased through the student portal.',
        'tags': ['React', 'Revision guides', 'Digital reading'],
        'impact': 'Gives KASNEB students a dedicated place to access and read their official revision guides.',
        'status': 'Live',
        'link': 'https://revision.kasneb.or.ke',
        'repo': '#',
    },
    {
        'id': 'kasneb-student-portal',
        'title': 'KASNEB Student Portal',
        'category': 'Student services',
        'description': 'An online self-service portal for KASNEB students, bringing account access, exam bookings, and revision-guide purchases into one place.',
        'tags': ['Student services', 'Exam bookings', 'Self-service'],
        'impact': 'Centralizes student services and access to KASNEB learning resources.',
        'status': 'Live',
        'link': 'https://online.kasneb.or.ke',
        'repo': '#',
    },
    {
        'id': 'pulse-uptime',
        'title': 'Pulse Uptime',
        'category': 'Uptime monitoring',
        'description': 'A self-hosted dashboard for monitoring website availability, with background health checks, incident history, and email alerts for outages and recovery.',
        'tags': ['Node.js', 'SQLite', 'Email alerts'],
        'impact': 'Keeps service health and outage notifications in one dashboard, hosted on my own server.',
        'status': 'Live',
        'link': 'https://uptime.calebmayaka.com',
        'repo': '#',
    },
]

experience = [
    {
        'role': 'Full-Stack Developer',
        'company': 'Independent Projects',
        'period': 'Current',
        'description': 'Building portfolio-ready web apps with Django, JavaScript, polished interfaces, and maintainable structure.',
        'achievements': [
            'Created multi-page Django experiences with reusable templates and data-driven content.',
            'Designed responsive UI systems for project galleries, contact flows, and content-heavy pages.',
            'Focused on clear code organization so projects can grow beyond the first version.',
        ],
    },
    {
        'role': 'Backend & Web Systems Learner',
        'company': 'Personal Lab',
        'period': 'Recent',
        'description': 'Practicing the foundations behind reliable web products: routing, views, templates, data, and deployment basics.',
        'achievements': [
            'Explored Django project structure, static assets, and app-based development.',
            'Built reusable content patterns for profiles, projects, skills, and case studies.',
            'Kept content modular so new professional details can be added cleanly.',
        ],
    },
    {
        'role': 'Frontend Builder',
        'company': 'Design Recreation Work',
        'period': 'Ongoing',
        'description': 'Recreating modern portfolio styles with semantic HTML, custom CSS, and small JavaScript interactions.',
        'achievements': [
            'Translated a dynamic design direction into a lighter Django-rendered implementation.',
            'Implemented cards, timelines, modal details, mobile navigation, and animated reveals.',
            'Balanced visual polish with straightforward maintainability.',
        ],
    },
]

case_studies = [
    {
        'id': 'django-portfolio',
        'title': 'Django Portfolio Rebuild',
        'category': 'Web Presence',
        'duration': '1 week sprint',
        'role': 'Designer & Developer',
        'description': 'Rebuilding the portfolio into a clean Django site with editable content and a modern visual system.',
        'problem': 'The starting Django project needed a stronger visual system, clearer content structure, and an easier editing path.',
        'solution': 'Create a Django-native app with shared templates, local static assets, data-driven content, and lightweight JavaScript interactions.',
        'results': ['Six public pages', 'Clear site structure', 'Editable content', 'Responsive portfolio UI'],
        'tags': ['Django', 'Templates', 'Static Files', 'UX'],
    },
    {
        'id': 'client-dashboard',
        'title': 'Client Dashboard Concept',
        'category': 'SaaS UX',
        'duration': 'Prototype',
        'role': 'Product Developer',
        'description': 'A dashboard concept for client projects, tasks, documents, and simple status reporting.',
        'problem': 'Small teams often manage client updates across too many channels, making progress difficult to see.',
        'solution': 'Centralize key project information into a calm dashboard with task status, files, and next steps.',
        'results': ['Clear task states', 'Fast scanning', 'Better handoff flow', 'Lower admin load'],
        'tags': ['Django', 'Dashboards', 'Admin', 'Workflow'],
    },
    {
        'id': 'ai-support',
        'title': 'AI Support Workflow',
        'category': 'Automation',
        'duration': 'Concept',
        'role': 'AI Integrator',
        'description': 'A practical AI workflow for classifying messages, drafting replies, and surfacing relevant help content.',
        'problem': 'Support messages can repeat often, but teams still need consistent, human-reviewed answers.',
        'solution': 'Use AI as a drafting and routing layer while keeping final responses under human control.',
        'results': ['Faster triage', 'Reusable knowledge', 'Consistent tone', 'Human approval'],
        'tags': ['AI', 'Automation', 'APIs', 'Support'],
    },
]

testimonials = [
    {
        'quote': 'Caleb\'s portfolio is being shaped to communicate craft, clarity, and momentum from the first screen.',
        'name': 'Portfolio Review',
        'title': 'Design feedback note',
    },
    {
        'quote': 'The structure is ready to grow with deeper project notes, writing, and collaboration outcomes.',
        'name': 'Content Review',
        'title': 'Portfolio planning note',
    },
]
