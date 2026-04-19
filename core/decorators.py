from django.shortcuts import redirect

def owner_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'owner':
            return redirect('/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper