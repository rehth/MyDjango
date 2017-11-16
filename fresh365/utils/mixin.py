from django.views.generic import View
from django.contrib.auth.decorators import login_required


class LoginRequiredMixin(View):
    """用作检验是否登录"""
    @classmethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        return login_required(view)
