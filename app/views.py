from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404,redirect
from django.views.generic import ListView, DetailView,View
from django.utils import timezone
from .models import *
from .forms import CheckoutForm

# Create your views here.

# def home(request):
# 	context = {
# 		"items" : Item.objects.all()
# 	}
# 	return render(request, 'home.html', context)

class HomeView(ListView):
	model = Item
	paginate_by = 10
	template_name = "home.html" 

class ItemDetailView(DetailView):
	model = Item
	template_name = "product.html"

class OrderSummaryView(LoginRequiredMixin,View):
	def get(self, *args, **kwargs):

		try:

			order = Order.objects.get(user=self.request.user, ordered=False)
			context = {
				'object':order
			}
			return render(self.request, 'order_summary.html',context)

		except ObjectDoesNotExist:
			messages.error(self.request, "You do not have an active order")
			return redirect('/')
	

#CODE USED TO ADD TO CART IN DJANGO
@login_required
def add_to_cart(request, slug):
	item = get_object_or_404(Item, slug=slug)
	order_item, created = OrderItem.objects.get_or_create(
		item=item,
		user = request.user,
		ordered = False
		)
	order_qs = Order.objects.filter(user=request.user, ordered=False)

	if order_qs.exists():
		order =order_qs[0]
		#to check if the item is in the order
		if order.item.filter(item__slug=item.slug).exists():
			order_item.quantity += 1
			order_item.save()
			messages.info(request, "Item quantity was updated successfully")
			return redirect("app:order-summary")

		else:
			order.item.add(order_item)
			messages.info(request, "Item added successfully")
			return redirect("app:order-summary")

		
	else:
		ordered_date = timezone.now()
		order = Order.objects.create(user=request.user,ordered_date=ordered_date)
		order.item.add(order_item)
		messages.info(request, "Item added successfully")
		return redirect("app:order-summary")

@login_required
def remove_from_cart(request ,slug):
	item = get_object_or_404(Item, slug=slug)

	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order =order_qs[0]
		#to check if the item is in the order
		if order.item.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
				item=item,
				user = request.user,
				ordered = False
				)[0]
			order.item.remove(order_item)
			messages.info(request, "Item removed successfully")
			return redirect("app:order-summary")
		else:
			messages.info(request, "Item was not in your cart")
			return redirect("app:product",slug=slug)
						
	else:
		#add a message the user does'nt have an order
		messages.info(request, "You do not have an order")
		return redirect("app:product",slug=slug)


@login_required
def remove_single_item_from_cart(request ,slug):
	item = get_object_or_404(Item, slug=slug)

	order_qs = Order.objects.filter(user=request.user, ordered=False)
	if order_qs.exists():
		order =order_qs[0]
		#to check if the item is in the order
		if order.item.filter(item__slug=item.slug).exists():
			order_item = OrderItem.objects.filter(
				item=item,
				user = request.user,
				ordered = False
				)[0]
			if order_item.quantity >1:
				order_item.quantity -= 1
				order_item.save()
			else:
				order.item.remove(order_item)
			messages.info(request, "Item quantity was updated")
			return redirect("app:order-summary")
		else:
			messages.info(request, "Item was not in your cart")
			return redirect("app:product",slug=slug)
						
	else:
		#add a message the user does'nt have an order
		messages.info(request, "You do not have an order")
		return redirect("app:product",slug=slug)


	

class CheckoutView(View):

	def get(self, *args, **kwargs):
		form = CheckoutForm()
		context = {
		'form': form
		}
		#form
		return render(self.request, 'checkout.html',context)

	def post(self, *args, **kwargs):

		form = CheckoutForm(self.request.POST or None)
		try:

			order = Order.objects.get(user=self.request.user, ordered=False)
			if form.is_valid():
				street_address= form.cleaned_data.get('street_address')
				apartment_address= form.cleaned_data.get('apartment_address')
				country= form.cleaned_data.get('country')
				zips= form.cleaned_data.get('zips')
				## ADD FUNCTIONALITY TO THIS FIELDS 
				# same_shipping_address= form.cleaned_data.get('same_shipping_address')
				# save_info= form.cleaned_data.get('save_info')
				payment_option= form.cleaned_data.get('payment_option')

				billing_address = BillingAddress(
					user = self.request.user,
					street_address = street_address,
					apartment_address = apartment_address,
					country = country,
					zips = zips
					)
				billing_address.save()
				order.billing_address = billing_address
				order.save()
				## Add a Redirect to the selected billing payment
				return redirect("app:checkout")
			messages.warning(self.request, "Failed checkout")
			return redirect("app:checkout")
			

		except ObjectDoesNotExist:
			messages.error(self.request, "You do not have an active order")
			return redirect('app:order-summary')


class PaymentView(View):
	def get(self, *args, **kwargs):
		return render(self.request, "payment.html")
