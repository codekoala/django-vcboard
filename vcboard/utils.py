from django.template.defaultfilters import slugify

def unique_slug(string, klass, params={}, slug_field='slug'):
    """
    Determines a unique slug for any given object.  You must specify the string
    from which the original slug will be created, along with the class of 
    object that will be checked for unique slugs.  You may also specify other 
    conditions for the unique slugs.  For example, if you only want unique
    slugs within a given forum, you might pass in {'parent': self.parent} in 
    the models.py file.  Finally, you may specify the name of the slug field
    if it is not "slug".
    """

    slug = slugify(string)
    while True:
        params[slug_field] = slug
        if len(klass.objects.filter(**params)) == 0:
            return slug
        else:
            slug += '_'
