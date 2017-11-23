from django.shortcuts import render, redirect
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.core.urlresolvers import reverse

# Create your views here.


# /order
class OrderPlace(LoginRequiredMixin):
    def get(self, request):
        return redirect(reverse('cart:info'))

    def post(self, request):
        sku_ids = request.POST.getlist('sku_ids')
        # print(sku_ids)  ['5', '3', '4']
        return render(request, 'place_order.html')