from django.shortcuts import render

from .data import (
    case_studies,
    experience as experience_items,
    nav_items,
    profile,
    projects as project_items,
    skills,
    social_links,
    stats,
    tech_stack,
    testimonials,
)


def base_context(active):
    return {
        'active': active,
        'profile': profile,
        'nav_items': nav_items,
        'social_links': social_links,
    }


def home(request):
    context = {
        **base_context('home'),
        'page_title': f"{profile['name']} | {profile['role']}",
        'stats': stats,
        'skills': skills,
        'projects': project_items[:3],
        'experience': experience_items,
        'testimonials': testimonials,
    }
    return render(request, 'portfolio/home.html', context)


def about(request):
    context = {
        **base_context('about'),
        'page_title': f"About | {profile['name']}",
        'skills': skills,
        'tech_stack': tech_stack,
        'stats': stats,
    }
    return render(request, 'portfolio/about.html', context)


def experience(request):
    context = {
        **base_context('experience'),
        'page_title': f"Experience | {profile['name']}",
        'experience': experience_items,
        'tech_stack': tech_stack,
    }
    return render(request, 'portfolio/experience.html', context)


def projects(request):
    context = {
        **base_context('projects'),
        'page_title': f"Projects | {profile['name']}",
        'projects': project_items,
    }
    return render(request, 'portfolio/projects.html', context)


def case_studies(request):
    context = {
        **base_context('case_studies'),
        'page_title': f"Case Studies | {profile['name']}",
        'case_studies': case_studies,
    }
    return render(request, 'portfolio/case_studies.html', context)


def contact(request):
    context = {
        **base_context('contact'),
        'page_title': f"Contact | {profile['name']}",
        'skills': skills,
    }
    return render(request, 'portfolio/contact.html', context)
