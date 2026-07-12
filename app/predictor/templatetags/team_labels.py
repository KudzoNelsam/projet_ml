from django import template
from predictor.services import french_team_label

register = template.Library()

@register.filter
def team_fr(value):
    return french_team_label(value) if value else value
