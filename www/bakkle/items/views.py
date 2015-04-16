from django.shortcuts import render

import json
import datetime

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Items, BuyerItem
from account.models import Account

@csrf_exempt
def index(request):
    item_list = Items.objects.all()
    context = {
        'item_list': item_list,
    }
    return render(request, 'items/index.html', context) 

@csrf_exempt
def detail(request, item_id):
    item = get_object_or_404(Items, pk=item_id)
    urls = item.image_urls.split(',');
    context = {
        'item': item,
        'urls': urls,
    }
    return render(request, 'items/detail.html', context) 

@csrf_exempt
@require_POST
def add_item(request):
    image_urls = request.POST.get('device_token', "").strip()
    title = request.POST.get('title', "").strip()
    description = request.POST.get('description', "").strip()
    location = request.POST.get('location').strip()
    seller_id = request.POST.get('account_id').strip()
    price = request.POST.get('price').strip()
    tags = request.POST.get('tags',"").strip()
    method = request.POST.get('method').strip()

    if (title == None or title == "") or (title == None or title == ""):
        return ""

    response_data = { "status":0 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
def edit_item(request):
    response_data = { "status":0 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
def feed(request):
    # TODO: need to confirm order to display, chrono?, closest? "magic"?
    # TODO: Add distance filtering here
    buyer_id = request.POST.get('account_id')
    items_viewed = BuyerItem.objects.filter(buyer = buyer_id)
    item_list = Items.objects.exclude(buyeritem = items_viewed).exclude(seller = buyer_id)
    response_data = "{\"status\": 1, \"feed\": " + serializers.serialize('json', item_list) + "}"
    return HttpResponse(response_data, content_type="application/json")

@csrf_exempt
@require_POST
def meh(request):
    return add_Item_To_Buyer_Items(request, BuyerItem.MEH)

@csrf_exempt
@require_POST
def want(request):
    return add_Item_To_Buyer_Items(request, BuyerItem.WANT)

@csrf_exempt
@require_POST
def hold(request):
    return add_Item_To_Buyer_Items(request, BuyerItem.HOLD)

@csrf_exempt
@require_POST
def report(request):
    item_id = request.POST.get('item_id')
    item = get_object_or_404(Items, pk=item_id)
    item.times_reported = item.times_reported + 1
    item.save()
    return add_Item_To_Buyer_Items(request, BuyerItem.REPORT)
    
def add_Item_To_Buyer_Items(request, status):
    buyer_id = request.POST.get('account_id')
    item_id = request.POST.get('item_id')

    if buyer_id == None or item_id == None:
        return "" # TODO: Need better response

    item = get_object_or_404(Items, pk=item_id)

    buyer_item = BuyerItem.objects.get_or_create(
        buyer = get_object_or_404(Account, pk=buyer_id),
        item = item,
        defaults = { 'status': status, 'confirmed_price': item.price })[0]
    buyer_item.status = status
    buyer_item.confirmed_price = item.price
    buyer_item.save()
    response_data = { 'status':1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
def reset(request):
    #TODO: hardcoded values
    item_expire_time=7 #days
    #TODO: Change to POST or DELETE
    Items.objects.all().delete()
    BuyerItem.objects.all().delete()
    i = Items(
        image_urls = "https://app.bakkle.com/img/b83bdbd.png",
        title = "Orange Push Mower",
        description = "Year old orange push mower. Some wear and sun fadding. Was kept outside and not stored in shed.",
        location = "39.417672,-87.330438",
        seller = get_object_or_404(Account, pk=1),
        price = 50.25,
        tags = "lawnmower, orange, somewear",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/b8348df.jpg",
        title = "Rabbit Push Mower",
        description = "Homemade lawn mower. Includes rabbit and water container.",
        location = "39.417672,-87.330438",
        seller = get_object_or_404(Account, pk=1),
        price = 10.99,
        tags = "lawnmower, homemade, rabbit",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/b8349df.jpg,https://app.bakkle.com/img/b8350df.jpg",
        title = "iPhone 6 Cracked",
        description = "iPhone 6. Has a cracked screen. Besides screen phone is in good condition.",
        location = "39.417672,-87.330438",
        seller = get_object_or_404(Account, pk=1),
        price = 65.99,
        tags = "iPhone6, cracked, damaged",
        method = Items.DELIVERY,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    # b = BuyerItem(
    #     buyer = i.seller,
    #     item = i,
    #     confirmed_price = i.price,
    #     status = BuyerItem.WANT )
    # b.save()

    print("Adding {}".format(i.title))
    return HttpResponse("resetting {}".format(i.title)) #change success value

