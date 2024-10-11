def selected_customer(request):
    return {'selected_customer': getattr(request, 'selected_customer', None)}
