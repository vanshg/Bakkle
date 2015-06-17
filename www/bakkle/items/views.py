from django.shortcuts import render

import base64
import datetime
import json
import md5
import os

import random

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from decimal import *
from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.core import serializers
from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.template import loader
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import BuyerItem
from .models import Items
from account.models import Account
from account.models import Device
from chat.models import Chat
from chat.models import Message
from common.decorators import authenticate
# from common.decorators import get_number_conversations_with_new_messages
from common.decorators import time_method
from django.conf import settings
import math;

MAX_ITEM_IMAGE = 5

config = {}
config['S3_BUCKET'] = 'com.bakkle.prod'
config['AWS_ACCESS_KEY'] = 'AKIAJIE2FPJIQGNZAMVQ' # server to s3
config['AWS_SECRET_KEY'] = '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'

config['AWS_ACCESS_KEY'] = 'AKIAJUCSHZSTNFVMEP3Q' # pethessa
config['AWS_SECRET_KEY'] = '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'

config['S3_URL'] = 'https://s3-us-west-2.amazonaws.com/com.bakkle.prod/'


#--------------------------------------------#
#               Web page requests            #
#--------------------------------------------#
@csrf_exempt
@time_method
def index(requestHandler):
    # List all items (this is for web viewing of data only)
    item_list = Items.objects.all()
    context = {
        'item_list': item_list,
    }
    return requestHandler.render('templates/items/index.html', item_list = item_list) 

@csrf_exempt
@time_method
def public_detail(request, item_id):
    # get the item with the item id (this is for web viewing of data only)
    item = get_object_or_404(Items, pk=item_id)
    urls = item.image_urls.split(',');
    context = {
        'item': item,
        'urls': urls,
    }
    return render(request, 'items/public_detail.html', context)

@staff_member_required
@csrf_exempt
@time_method
def detail(request, item_id):
    # get the item with the item id (this is for web viewing of data only)
    item = get_object_or_404(Items, pk=item_id)
    urls = item.image_urls.split(',');
    context = {
        'item': item,
        'urls': urls,
    }
    return render(request, 'items/detail.html', context)

@staff_member_required
@csrf_exempt
@time_method
def mark_as_spam(request, item_id):
    # Get the item
    item = Items.objects.get(pk=item_id)
    item.status = Items.SPAM
    item.save()

    item_list = Items.objects.all()
    context = {
        'item_list': item_list,
    }
    return render(request, 'items/index.html', context)

@staff_member_required
@csrf_exempt
@time_method
def mark_as_deleted(request, item_id):
    # Get the item id 
    item = Items.objects.get(pk=item_id)
    item.status = Items.DELETED
    item.save()

    item_list = Items.objects.all()
    context = {
        'item_list': item_list,
    }
    return render(request, 'items/index.html', context)

#--------------------------------------------#
#               Item Methods                 #
#--------------------------------------------#
@csrf_exempt
@require_POST
@authenticate
@time_method
def add_item(request):
    # Get the authentication code
    auth_token = request.GET.get('auth_token')

    # TODO: Handle location
    # Get the rest of the necessary params from the request
    title = request.GET.get('title', "")
    description = request.GET.get('description', "")
    location = request.GET.get('location')
    seller_id = auth_token.split('_')[1]
    price = request.GET.get('price')
    tags = request.GET.get('tags',"")
    method = request.GET.get('method')
    notifyFlag = request.GET.get('notify')

    # Get the item id if present (If it is present an item will be edited not added)
    item_id = request.GET.get('item_id', "")

    # Ensure that required fields are present otherwise send back a failed status
    if (title == None or title == "") or (tags == None or tags == "") or (price == None or price == "") or (method == None or method == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Ensure that the price can be converted to a decimal otherwise send back a failed status
    try:
        price = Decimal(price)
    except ValueError:
        response_data = { "status":0, "error": "Price was not a valid decimal." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Check for the image params. The max number is 5 and is defined in settings
    image_urls = imgupload(request, seller_id)

    TWOPLACES = Decimal(10) ** -6

    if (item_id == None or item_id == ""):
        # Create the item
        item = Items.objects.create(
            title = title,
            seller_id = seller_id,
            description = description,
            longitude = Decimal(location.split(",")[0]).quantize(TWOPLACES),
            latitude = Decimal(location.split(",")[1]).quantize(TWOPLACES),
            price = price,
            tags = tags,
            method = method,
            image_urls = image_urls,
            status = Items.ACTIVE)
        item.save()
        if(notifyFlag == None or notifyFlag == "" or int(notifyFlag) != 0):
            notify_all_new_item("New: ${} - {}".format(item.price, item.title))
    else:
        # Else get the item
        try:
            item = Items.objects.get(pk=item_id)
        except Item.DoesNotExist:
            item = None
            response_data = {"status":0, "error":"Item {} does not exist.".format(item_id)}
            return HttpResponse(json.dumps(response_data), content_type="application/json")

        # TODO: fix this
        # Remove all previous images
        # old_urls = item.image_urls.split(",")
        # for url in old_urls:
        #     # remove image from S3
        #     handle_delete_file_s3(url)

        # Update item fields
        item.title = title
        item.description = description
        item.tags = tags
        item.price = price
        item.method = method
        item.image_urls = image_urls
        item.save()

    response_data = { "status":1, "item_id":item.id }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@time_method
def notify_all_new_item(message):
    # Get all devices

    if message == None or message == "":
        response_data = { "status": 0, "error": "No message supplied" }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    devices = Device.objects.filter() #todo: add active filter, add subscribed to notifications filter.

    # notify each device
    for device in devices:
        if device.auth_token != "":
            account_id = device.auth_token.split('_')[1]
            # lookup number of unread messages
            # badge = get_number_conversations_with_new_messages(account_id)
            device.send_notification(message, 1, "")

    response_data = { "status": 1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
@authenticate
@time_method
def delete_item(request):
    return update_status(request, Items.DELETED)


# This will only be called by the system if an Item has been reported X amount of times.
# TODO: implement this in the report 
def spam_item(request):
    return update_status(request, Items.SPAM)

@csrf_exempt
@require_POST
@authenticate
@time_method
def feed(request):

    MAX_ITEM_PRICE = 100;
    MAX_ITEM_DISTANCE = 100;
    RETURN_ITEM_ARRAY_SIZE = 20;
    
    auth_token = request.POST.get('auth_token')
    device_uuid = request.POST.get('device_uuid', "")
    user_location = request.POST.get('user_location', "")

    # TODO: Use these for filtering
    search_text = request.POST.get('search_text')
    filter_distance = int(request.POST.get('filter_distance'))
    filter_price = int(request.POST.get('filter_price'))

    # Check that all require params are sent and are of the right format
    if (auth_token == None or auth_token.strip() == "" or auth_token.find('_') == -1) or (user_location == None or user_location == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Check that location was in the correct format
    location = ""
    lat = 0;
    lon = 0;
    try: 
        positions = user_location.split(",")
        if len(positions) < 2:
            response_data = {"status":0, "error":"User location was not in the correct format."}
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            TWOPLACES = Decimal(10) ** -2
            lat = float(Decimal(positions[0]).quantize(TWOPLACES))
            lon = float(Decimal(positions[1]).quantize(TWOPLACES))
            location = str(lat) + "," + str(lon)
    except ValueError:
        response_data = { "status":0, "error": "Latitude or Longitude was not a valid decimal." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # get the account id 
    buyer_id = auth_token.split('_')[1]

    #horizontal range
    lonRange = filter_distance / (math.cos(lat/180 * math.pi) * 69.172)

    #vertical range
    latRange = filter_distance / 69.172

    #filter(longitude__lte = lon + lonRange).filter(longitude__gte = lon - lonRange).filter(latitude__lte = lat + latRange).filter(latitude__gte = lat + latRange)

    # get the account object and the device and update location
    try:
        account = Account.objects.get(id=buyer_id)
        account.user_location = location
        account.save()

        # Get the device
        device = Device.objects.get(account_id = buyer_id, uuid = device_uuid)
        device.user_location = location
        device.save()
    except Account.DoesNotExist:
        account = None
        response_data = {"status":0, "error":"Account {} does not exist.".format(buyer_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except Device.DoesNotExist:
        device = None
        response_data = {"status":0, "error":"Device {} does not exist.".format(device_uuid)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


    # get items
    items_viewed = BuyerItem.objects.filter(buyer = buyer_id)

    item_list = None
    users_list = None

    print(filter_price);
    print(filter_distance == MAX_ITEM_DISTANCE);
        
    if(search_text != None and search_text != ""):
        search_text.strip()


        #if filter price is 100+, ignore filter.
        if(filter_price == MAX_ITEM_PRICE):
            item_list = Items.objects.exclude(buyeritem = items_viewed).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).filter(Q(tags__contains=search_text) | Q(title__contains=search_text)).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
        else:
            item_list = Items.objects.exclude(buyeritem = items_viewed).filter(Q(price__lte = filter_price)).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).filter(Q(tags__contains=search_text) | Q(title__contains=search_text)).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
    else:
        
        #if filter price is 100+, ignore filter.
        if(filter_distance == MAX_ITEM_DISTANCE):
            if(filter_price == MAX_ITEM_PRICE):
                print 1;
                item_list = Items.objects.exclude(buyeritem = items_viewed).exclude(Q(seller__pk = buyer_id)).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
                users_list = Items.objects.filter(Q(seller__pk = buyer_id)).order_by('-post_date')[:1]
            else:
                print 2;
                item_list = Items.objects.exclude(buyeritem = items_viewed).exclude(Q(seller__pk = buyer_id)).filter(Q(price__lte = filter_price)).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
                users_list = Items.objects.filter(Q(seller__pk = buyer_id)).order_by('-post_date')[:1]
        else:
            if(filter_price == MAX_ITEM_PRICE):
                print 3;
                item_list = Items.objects.exclude(buyeritem = items_viewed).exclude(Q(seller__pk = buyer_id)).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).filter(longitude__lte = lon + lonRange).filter(longitude__gte = lon - lonRange).filter(latitude__lte = lat + latRange).filter(latitude__gte = lat + latRange).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
                users_list = Items.objects.filter(Q(seller__pk = buyer_id)).order_by('-post_date')[:1]
            else:
                print 4;
                item_list = Items.objects.exclude(buyeritem = items_viewed).exclude(Q(seller__pk = buyer_id)).filter(Q(price__lte = filter_price)).filter(Q(status = BuyerItem.ACTIVE) | Q(status = BuyerItem.PENDING)).filter(longitude__lte = lon + lonRange).filter(longitude__gte = lon - lonRange).filter(latitude__lte = lat + latRange).filter(latitude__gte = lat + latRange).order_by('-post_date')[:RETURN_ITEM_ARRAY_SIZE]
                users_list = Items.objects.filter(Q(seller__pk = buyer_id)).order_by('-post_date')[:1]
   
    item_array = []
    paginatedItems = Paginator(item_list, 100);
    numUserItems = 0;
    
    # show user's items before other items - place at top of array.
    if(not users_list is None and len(users_list) != 0):
        for item in users_list:
            if(len(BuyerItem.objects.filter(buyer__pk = buyer_id).filter(item__pk = item.pk)) == 0):
                item_dict = get_item_dictionary(item)
                item_array.append(item_dict)
    
    # add all other items - show after top user item
    page = 1;
    while len(item_array) < RETURN_ITEM_ARRAY_SIZE and page <= paginatedItems.num_pages:
        itemPage = paginatedItems.page(page);
        for item in itemPage.object_list:
            if (len(item_array) < RETURN_ITEM_ARRAY_SIZE):
                item_dict = get_item_dictionary(item)
                item_array.append(item_dict)
        
        page += 1;

    response_data = { 'status': 1, 'feed': item_array }
    print "returning feed list of size: " + str(len(item_array))
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
@authenticate
@time_method
def meh(request):
    return add_item_to_buyer_items(request, BuyerItem.MEH)

@csrf_exempt
@require_POST
@authenticate
@time_method
def sold(request):
    return add_item_to_buyer_items(request, BuyerItem.SOLD)

@csrf_exempt
@require_POST
@authenticate
@time_method
def want(request):
    item_id = request.POST.get('item_id')
    auth_token = request.POST.get('auth_token', "")
    buyer_id = auth_token.split('_')[1]

    # Check that all require params are sent and are of the right format
    if (item_id == None or item_id.strip() == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    try:
        buyer = Account.objects.get(pk=buyer_id)
    except Account.DoesNotExist:
        buyer = None
        response_data = {"status":0, "error":"Buyer {} does not exist.".format(buyer_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    try:
        item = Items.objects.get(pk=item_id)
    except Items.DoesNotExist:
        item = None
        response_data = {"status":0, "error":"Item {} does not exist.".format(item_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    chat = Chat.objects.get_or_create(
        item = item,
        buyer = buyer)[0]
    chat.start_time = datetime.datetime.now()
    chat.save()

    return add_item_to_buyer_items(request, BuyerItem.WANT)

@csrf_exempt
@require_POST
@authenticate
@time_method
def hold(request):
    return add_item_to_buyer_items(request, BuyerItem.HOLD)

@csrf_exempt
@require_POST
@authenticate
@time_method
def report(request):
    item_id = request.POST.get('item_id')

    # Check that all require params are sent and are of the right format
    if (item_id == None or item_id.strip() == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Get item and update the times reported
    try:
        item = Items.objects.get(pk=item_id)
    except Item.DoesNotExist:
        item = None
        response_data = {"status":0, "error":"Item {} does not exist.".format(item_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    item.times_reported = item.times_reported + 1
    item.save()

    return add_item_to_buyer_items(request, BuyerItem.REPORT)


#--------------------------------------------#
#            Buyer Item Methods              #
#--------------------------------------------#
@csrf_exempt
@require_POST
@authenticate
@time_method
def buyer_item_meh(request):
    return add_item_to_buyer_items(request, BuyerItem.MEH)

@csrf_exempt
@require_POST
@authenticate
@time_method
def buyer_item_want(request):
    return add_item_to_buyer_items(request, BuyerItem.WANT)

#--------------------------------------------#
#           Seller's Item Methods            #
#--------------------------------------------#
@csrf_exempt
@require_POST
@authenticate
@time_method
def get_seller_items(request):
    # Get the authentication code
    auth_token = request.POST.get('auth_token')
    seller_id = auth_token.split('_')[1]

    item_list = Items.objects.filter(Q(seller=seller_id, status=Items.ACTIVE) | Q(seller=seller_id, status=Items.PENDING))



    item_array = []
    # get json representaion of item array
    for item in item_list:
        # get the conversations involving this item
        chats = Chat.objects.filter(item=item)
        convos_with_new_message = 0
        # for convo in chats:
        #     messages = Message.objects.filter(viewed=None, buyer_seller_flag=True, chat=convo).count()
        #     if messages > 0:
        #         convos_with_new_message = convos_with_new_message + 1

        # get the buyer items for this item
        buyer_items = BuyerItem.objects.filter(item_id=item.id)
        number_of_views = 0
        number_of_meh = 0
        number_of_want = 0
        number_of_report = 0
        number_of_holding = 0
        for buyer_item in buyer_items:
            number_of_views = number_of_views + 1
            if buyer_item.status == BuyerItem.MEH:
                number_of_meh = number_of_meh + 1
            elif buyer_item.status == BuyerItem.REPORT:
                number_of_report = number_of_report + 1
            elif buyer_item.status == BuyerItem.HOLD:
                number_of_holding = number_of_holding + 1
            elif buyer_item.status == BuyerItem.WANT or buyer_item.status == BuyerItem.NEGOTIATING or buyer_item.status == BuyerItem.PENDING:
                number_of_want = number_of_want + 1


        # create the dictionary for the item and append it
        item_dict = get_item_dictionary(item)
        item_dict['convos_with_new_message'] = convos_with_new_message
        item_dict['number_of_views'] = number_of_views
        item_dict['number_of_meh'] = number_of_meh
        item_dict['number_of_want'] = number_of_want
        item_dict['number_of_holding'] = number_of_holding
        item_dict['number_of_report'] = number_of_report
        item_array.append(item_dict)

    # create json string
    response_data = {'status': 1, 'seller_garage': item_array}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
@authenticate
@time_method
def get_seller_transactions(request):
    # Get the authentication code
    auth_token = request.POST.get('auth_token')
    seller_id = auth_token.split('_')[1]

    item_list = Items.objects.filter(seller=seller_id, status=Items.SOLD)

    item_array = []
    # get json representaion of item array
    for item in item_list:
        item_dict = get_item_dictionary(item)
        item_array.append(item_dict)

    # create json string
    response_data = {'status': 1, 'seller_history': item_array}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

#--------------------------------------------#
#           Buyer's Item Methods             #
#--------------------------------------------#
@csrf_exempt
@require_POST
@authenticate
@time_method
def get_buyers_trunk(request):
    # Get the authentication code
    auth_token = request.POST.get('auth_token')
    buyer_id = auth_token.split('_')[1]

    item_list = BuyerItem.objects.filter(Q(buyer=buyer_id, status=BuyerItem.WANT) | Q(buyer=buyer_id, status=BuyerItem.PENDING) | Q(buyer=buyer_id, status=BuyerItem.NEGOTIATING))

    item_array = []
    # get json representaion of item array
    for item in item_list:
        item_dict = get_buyer_item_dictionary(item)
        item_array.append(item_dict)

    response_data = { 'status': 1, 'buyers_trunk': item_array }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
@authenticate
@time_method
def get_holding_pattern(request):
    # Get the authentication code
    auth_token = request.POST.get('auth_token')
    buyer_id = auth_token.split('_')[1]

    item_list = BuyerItem.objects.filter(buyer=buyer_id, status=BuyerItem.HOLD)

    item_array = []
    # get json representaion of item array
    for item in item_list:
        item_dict = get_buyer_item_dictionary(item)
        item_array.append(item_dict)

    response_data = { 'status': 1, 'holding_pattern': item_array}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
@require_POST
@authenticate
@time_method
def get_buyer_transactions(request):
    # Get the authentication code
    auth_token = request.POST.get('auth_token')
    buyer_id = auth_token.split('_')[1]

    item_list = BuyerItem.objects.filter(buyer=buyer_id, status=BuyerItem.SOLD_TO)

    item_array = []
    # get json representaion of item array
    for item in item_list:
        item_dict = get_buyer_item_dictionary(item)
        item_array.append(item_dict)

    response_data = { 'status': 1, 'buyer_history': item_array}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

#--------------------------------------------#
#             Helper Functions               #
#--------------------------------------------#
# Helper for uploading image to S3
def handle_file_s3(image_key, f):
    print "HERE"
    image_string = ""
    for chunk in f.chunks():
        image_string = image_string + chunk

    conn = S3Connection(config['AWS_ACCESS_KEY'], config['AWS_SECRET_KEY'])
    #bucket = conn.create_bucket('com.bakkle.prod')
    bucket = conn.get_bucket(config['S3_BUCKET'])
    k = Key(bucket)
    image_key = config['S3_BUCKET'] + "_" + image_key
    k.key = image_key
    # http://boto.readthedocs.org/en/latest/s3_tut.html
    k.set_contents_from_string(image_string)
    k.set_acl('public-read')
    print config['S3_URL'] + image_key
    return config['S3_URL'] + image_key
    # TODO: Setup connection pool and queue for uploading at volume

#TODO: Fix this
def handle_delete_file_s3(image_path):
    file_parts = image_path.split("_")
    image_key = image_path.replace(config['S3_URL'], "")
    bucket_name = config['S3_BUCKET']
    if (len(file_parts) == 3):
        bucket_name = file_parts[0]
    conn = S3Connection(config['AWS_ACCESS_KEY'], config['AWS_SECRET_KEY'])
    #bucket = conn.create_bucket('com.bakkle.prod')
    bucket = conn.get_bucket(bucket_name)
    print(image_key)
    k = bucket.get_key(image_key)
    k.delete()

# Helper to handle image uploading
def imgupload(request, seller_id):
    image_urls = ""
    #import pdb; pdb.set_trace()
    
    print(request)

    for i in request.FILES.getlist('image'):
        #i = request.FILES['image']
        uhash = hex(random.getrandbits(128))[2:-1]
        image_key = "{}_{}.jpg".format(seller_id, uhash)
        filename = handle_file_s3(image_key, i)
        if image_urls == "":
            image_urls = filename
        else:
            image_urls = image_urls + "," + filename
    return image_urls

# Helper for creating buyer items
def add_item_to_buyer_items(request, status):
    auth_token = request.POST.get('auth_token', "")
    item_id = request.POST.get('item_id', "")
    view_duration = request.POST.get('view_duration',"")
    buyer_item_id = request.POST.get('buyer_item_id', "")

    # Check that all require params are sent and are of the right format
    if (view_duration == None or view_duration.strip() == "") or (auth_token == None or auth_token.strip() == "" or auth_token.find('_') == -1) or (item_id == None or item_id.strip() == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    
    try:
        view_duration = Decimal(view_duration)
    except ValueError:
        response_data = { "status":0, "error": "Price was not a valid decimal." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # get the account id 
    buyer_id = auth_token.split('_')[1]



    # get the item
    try:
        item = Items.objects.get(pk=item_id)
    except Item.DoesNotExist:
        item = None
        response_data = {"status":0, "error":"Item {} does not exist.".format(item_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    #check if item already sold - if so, return an error:
    print(item.status);
    if(item.status == Items.SOLD):
        item = None
        response_data = {"status":0, "error":"Item has already been sold."}
        return HttpResponse(json.dumps(response_data), content_type="application/json")


    try:
        account = Account.objects.get(pk=buyer_id)
        # Create or update the buyer item
        try:
            buyer_item = BuyerItem.objects.get(item = item.pk, buyer = buyer_id)
        except BuyerItem.DoesNotExist:

            buyer_item = BuyerItem.objects.create(
                buyer = account,
                item = item,
                status = status, 
                confirmed_price = item.price,
                view_duration = 0)

            # If the item seller is the same as the buyer mark it as their item instead of the status
            # TODO: Eventually put this back in to prevent errors from user trying to buy their own item
            # if(str(item.seller.id) == str(buyer_id)):
            #     print("Are same")
            #     buyer_item.status = BuyerItem.MY_ITEM
            # else:
            #     buyer_item.status = status


        if (status == BuyerItem.SOLD):
            buyer_item.accepted_sale_price = buyer_item.confirmed_price
            item.status = Items.SOLD
            item.save()
        else:
            buyer_item.confirmed_price = item.price

        buyer_item.status = status
        buyer_item.view_duration = view_duration
        buyer_item.save()

    except Account.DoesNotExist:
        account = None
        response_data = {"status":0, "error":"Account {} does not exist.".format(buyer_id)}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    
    

    response_data = { 'status':1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Helper for updating Item Statuses
def update_status(request, status):
    # Get the item id 
    item_id = request.POST.get('item_id', "")

    # Ensure that required fields are present otherwise send back a failed status
    if (item_id == None or item_id == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Get the item
    item = Items.objects.get(pk=item_id)
    item.status = status
    item.save()
    response_data = { "status":1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Helper for making an Item into a dictionary for JSON
def get_item_dictionary(item):
    images = []
    hashtags = []

    urls = item.image_urls.split(",")
    for url in urls:
        if url != "" and url != " ":
            images.append(url)

    tags = item.tags.split(",")
    for tag in tags:
        if tag != "" and tag != " ":
            hashtags.append(tag)

    seller_dict = get_account_dictionary(item.seller)
    item_dict = {'pk':item.pk, 
        'description': item.description, 
        'seller': seller_dict,
        'image_urls': images,
        'tags': hashtags,
        'title': item.title,
        'location': str(item.latitude) + "," + str(item.longitude),
        'price': str(item.price),
        'method': item.method,
        'status': item.status,
        'post_date': item.post_date.strftime("%Y-%m-%d %H:%M:%S")}
    return item_dict

# Helper for getting account information for items for JSON
# TODO: may need to add more fields
def get_account_dictionary(account):
    seller_dict = {'pk': account.pk, 
        'display_name': account.display_name, 
        'seller_rating': account.seller_rating,
        'buyer_rating': account.buyer_rating,
        'user_location': account.user_location,
        'facebook_id': account.facebook_id }
    return seller_dict

# Helper for making a BuyerItem into a dictionary for JSON
def get_buyer_item_dictionary(buyer_item):
    buyer_dict = get_account_dictionary(buyer_item.buyer)
    item_dict = get_item_dictionary(buyer_item.item)

    buyer_item_dict = {'pk': buyer_item.pk,
        'view_time': buyer_item.view_time.strftime("%Y-%m-%d %H:%M:%S"),
        'view_duration': str(buyer_item.view_duration),
        'status': buyer_item.status,
        'confirmed_price': str(buyer_item.confirmed_price),
        'accepted_sale_price': buyer_item.accepted_sale_price,
        'item': item_dict,
        'buyer': buyer_dict}
    return buyer_item_dict

# Helper to return the delivery methods for items
@csrf_exempt
@require_POST
@authenticate
def get_delivery_methods(request):
    response_data = { 'status': 1, 'deliver_methods': (dict(Items.METHOD_CHOICES)).values()}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

#--------------------------------------------#
#               Testing Items                #
#--------------------------------------------#
# TODO: Remove eventually. Testing data.
@csrf_exempt
def reset(request):
    #TODO: hardcoded values
    item_expire_time=7 #days
    auth_token = request.POST.get('auth_token')
    buyer_id = auth_token.split('_')[1]
    BuyerItem.objects.filter(buyer=buyer_id).delete()
    response_data = { "status":1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

@csrf_exempt
def reset_items(request):
    BuyerItem.objects.all().delete()
    Items.objects.all().delete()
    # create dummy account
    try:
        a = Account.objects.get(
            facebook_id="1020420",
            display_name="Goodwill Industries",
            email="testseller@bakkle.com" )
    except Account.DoesNotExist:
        a = Account(
            facebook_id="1020420",
            display_name="Goodwill Industries",
            email="testseller@bakkle.com",
            user_location="39.417672,-87.330438", )
        a.save()

    # create dummy device
    try:
        d = Device.objects.get_or_create(
            uuid = "E6264D84-C395-4132-8C63-3EF051480191",
            account_id= a,
            apns_token = "<224c36d9 4de49676 27c42676 ee3ba0a3 33adf555 79259e36 182abf83 8b86a35b>",
            ip_address = "000.000.000.00",
            notifications_enabled = True,
            auth_token = "asdfasdfasdfasdf_{}".format(a.id),
            app_version = "16" )[0]
        d.save()
    except Account.DoesNotExist:
        d = Device(
            uuid = "E6264D84-C395-4132-8C63-3EF051480191",
            account_id= a,
            apns_token = "<224c36d9 4de49676 27c42676 ee3ba0a3 33adf555 79259e36 182abf83 8b86a35b>",
            ip_address = "000.000.000.00",
            notifcations_enabled = True,
            auth_token = "asdfasdfasdfasdf_{}".format(a.id),
            app_version = "16" )
        d.save()

    i = Items(
        image_urls = "https://app.bakkle.com/img/b83bdbd.png",
        title = "Orange Push Mower",
        description = "Year old orange push mower. Some wear and sun fadding. Was kept outside and not stored in shed.",
        latitude = 42.40,
        longitude = 73.45,
        seller = a,
        price = 50.25,
        tags = "lawnmower, orange, somewear",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/WP_20150417_09_47_27_Pro.jpg",
        title = "Oil change",
        description = "will change your cars oil at your location, $ 19.95.",
        latitude = 35.05,
        longitude = 106.39,
        seller = a,
        price = 19.95,
        tags = "service, oil change",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00e0e_5WQCcunAcn_600x450.jpg",
        title = "Flat screen LED TV",
        description = "Flat screen LED LCD TV. Brand new in box, 4 HDMI ports and Netflix built in.",
        latitude = 35.11,
        longitude = 101.50,
        seller = a,
        price = 107.00,
        tags = "tv, led, netflix",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00n0n_eerJtWHsBKc_600x450.jpg",
        title = "15\" MacBook pro",
        description = "MacBook Pro 15\" Mid 2014 i7. 2.2 GHz, 16 GB RAM, 256 GB SSD. Very little use, needed a lighter model so switched to MacBook air. Includes original box, power cord, etc.",
        latitude = 61.13,
        longitude = 149.54,
        seller = a,
        price = 999.00,
        tags = "mac, apple, macbook, macbook pro",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00n0n_gonFpgUcRAe_600x450.jpg",
        title = "Paint ball gun",
        description = "Gun only, no CO2 tank. Needs new HPR piston",
        latitude = 33.45,
        longitude = 84.23,
        seller = a,
        price = 40.99,
        tags = "paintball, gun, bump paintball",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00O0O_kOqfijcw7FL_600x450.jpg",
        title = "Business law text book",
        description = "Business law text and cases, clarkson, miller, jentz, 11th edition. No marks or highlighting.",
        latitude = 30.16,
        longitude = 97.44,
        seller = a,
        price = 40.99,
        tags = "textbook, business law",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00P0P_dcFyXMBIkYE_600x450.jpg",
        title = "Baseball mitt",
        description = "Louisville slugger baseball mitt, mint condition.",
        latitude = 44.47,
        longitude = 117.50,
        seller = a,
        price = 30.00,
        tags = "baseball mitt",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00s0s_49F9D9EnAJ3_600x450.jpg",
        title = "Bicycle",
        description = "Pure fix fixie bicycle.",
        latitude = 39.18,
        longitude = 76.38,
        seller = a,
        price = 300,
        tags = "bicycle",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00T0T_f1xeeb2KYxA_600x450.jpg",
        title = "Canon 50D",
        description = "Canon 50D digital camera. Comes with f1.8 50mm lens.",
        latitude = 44.48,
        longitude = 68.47,
        seller = a,
        price = 30.00,
        tags = "canon, 50d, digital camera",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00u0u_hj2g60Tn2D7_600x450.jpg",
        title = "iPhone 5",
        description = "White Apple iphone 5. Unlocked",
        latitude = 33.30,
        longitude = 86.50,
        seller = a,
        price = 200.00,
        tags = "apple, iphone, iphone 5",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00V0V_kQXPgLCzkEl_600x450.jpg",
        title = "weights",
        description = "Premium adjustable hand barbell weight set.",
        latitude = 46.48,
        longitude = 100.47,
        seller = a,
        price = 300.00,
        tags = "weights, barbell",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00W0W_hCYzWAyYAvP_600x450.jpg",
        title = "Blender",
        description = "Blender, used. Runs great. 5 speeds with turbo",
        latitude = 43.36,
        longitude = 116.13,
        seller = a,
        price = 12.00,
        tags = "blender",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00404_8sCApbm5Bvc_600x450.jpg",
        title = "Playstation 2",
        description = "Playstation 2 with controller. Broken, needs laser cleaning. Won't read discs.",
        latitude = 42.21,
        longitude = 71.5,
        seller = a,
        price = 45.00,
        tags = "sony, playstation, controller",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00808_k0TscttMik5_600x450.jpg",
        title = "Baseball bat",
        description = "Basic home security system.",
        latitude = 42.55,
        longitude = 78.50,
        seller = a,
        price = 10.00,
        tags = "baseball, security, bat",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/00909_iVAvBfYmpNm_600x450.jpg",
        title = "Gas grille",
        description = "Propane barbeque grill with side burner. 2 years old worth $200 from Lowes. Full propane bottle included.",
        latitude = 51.1,
        longitude = 114.1,
        seller = a,
        price = 10.00,
        tags = "propane, gas, grille, barbeque, bbq",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/01313_fXdf3fNJDJC_600x450.jpg",
        title = "Marketing textbooks",
        description = "MKTG marketing text (instructor edition) by Lam, hair, mcdaniel and Essentials of Entrepreneurship and Small Business Management by Normal M. Scarborough (7th global edition).",
        latitude = 32.26,
        longitude = 104.15,
        seller = a,
        price = 175.00,
        tags = "marketing, textbooks",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/01313_gsH7Yan7PYA_600x450.jpg",
        title = "Nike shoes",
        description = "Nike women's air max shoes size 6 1/2. Never worn outside.",
        latitude = 32.47,
        longitude = 79.56,
        seller = a,
        price = 90.00,
        tags = "shoes, nike, womens",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/b8348df.jpg",
        title = "Rabbit Push Mower",
        description = "Homemade lawn mower. Includes rabbit and water container.",
        latitude = 38.21,
        longitude = 81.38,
        seller = a,
        price = 10.99,
        tags = "lawnmower, homemade, rabbit",
        method = Items.PICK_UP,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()
    i = Items(
        image_urls = "https://app.bakkle.com/img/b8349df.jpg",
        title = "iPhone 6 Cracked",
        description = "iPhone 6. Has a cracked screen. Besides screen phone is in good condition.",
        latitude = 35.14,
        longitude = 80.50,
        seller = a,
        price = 65.99,
        tags = "iPhone6, cracked, damaged",
        method = Items.DELIVERY,
        status = Items.ACTIVE,
        post_date = datetime.datetime.now,
        times_reported = 0 )
    i.save()

    print("Adding {}".format(i.title))
    return HttpResponse("resetting {}".format(i.title)) #change success value

