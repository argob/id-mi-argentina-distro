"""Template tags custom"""

#Django
from django import template
from django.conf import settings


register = template.Library()

def get_setting(name):
    return getattr(settings, name, None)

register.simple_tag(get_setting)

@register.simple_tag
def get_area_code(phone_number):
    """
    Following suggested RFC 3966 protocol by open id
    expect: +111-1111-111111 format
    """
    if '-' in phone_number:
        phone_split = phone_number.split('-')
        if len(phone_split)  > 2:
            # if had country code
            return phone_split[1]
        return phone_split[0]
    return phone_number

@register.simple_tag
def get_phone_number(phone_number):
    """
    Following suggested RFC 3966 protocol by open id
    expect: +111-1111-111111 format
    """
    if '-' in phone_number:
        phone_split = phone_number.split('-')
        if len(phone_split) > 2:
            #if had country code
            return phone_split[2]
        return phone_split[1]
    return phone_number

@register.simple_tag
def dniformat(dni):
    if not ('.' in dni) and len(dni) == 8:
        return dni[:2] + '.' + dni[2:5] + '.' + dni[5:8]
    elif not ('.' in dni) and len(dni) == 7:
        return dni[:1] + '.' + dni[1:4] + '.' + dni[4:7]
    elif not ('.' in dni) and len(dni) < 7:
        return dni[:3] + '.' + dni[3:6]

    return dni

@register.simple_tag
def birthdateformat(birthdate):
    year, month, day = birthdate.split("-")
    birthdate = day + '/' + month + '/' + year

    return birthdate
