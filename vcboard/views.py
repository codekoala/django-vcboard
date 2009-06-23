from django.shortcuts import render_to_response
from django.template import RequestContext

def show_forum(request, path, template='vcboard/forum_detail.html'):
    """
    Displays a forum with its subforums and topics, if any
    """
    data = {}

    return render_to_response(template, data, context_instance=RequestContext(request))

