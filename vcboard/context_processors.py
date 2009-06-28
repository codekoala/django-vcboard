def site_name(request):
    from vcboard import config
    return {
        'session': request.session,
        'VCBOARD_NAME': config('general', 
                            'site_name',
                            default='VCBoard'),
    }
