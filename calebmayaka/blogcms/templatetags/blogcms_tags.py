from django import template

from blogcms.utils import embed_url


register = template.Library()
register.filter(name='embed_url')(embed_url)
