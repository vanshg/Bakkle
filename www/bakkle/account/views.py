from django.shortcuts import render

import datetime
import json
import md5

from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Account, Device
from items.models import Items, BuyerItem
from common import authenticate

# Show a list of all accounts in the system.
@csrf_exempt
def index(request):
    account_list = Account.objects.all()
    context = {
        'account_list': account_list,
    }
    return render(request, 'account/index.html', context)

# Login to account using Facebook
@csrf_exempt
@require_POST
def login_facebook(request):
    facebook_id = request.POST.get('user_id', "")
    device_uuid = request.POST.get('device_uuid', "")

    # Check that all required params are sent
    # Check that all required fields are sent
    if (facebook_id == None or facebook_id.strip() == "") or (device_uuid == None or device_uuid.strip() == ""): 
        response_data = {"status":0, "error":"A required parameter was not provided."}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Get the account for that facebook ID and it's associated device
    account = get_object_or_404(Account, facebook_id=facebook_id)
    device = device_register(get_client_ip(request), device_uuid, account)

    # Create authentication token
    login_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Set authentication token and save it
    device.auth_token = md5.new(login_date).hexdigest() + "_" + str(account.id)
    device.save()

    response_data = {"status":1, "auth_token": device.auth_token }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Logout of account
@csrf_exempt
@require_POST
def logout(request):
    auth_token = request.POST.get('auth_token', "")
    device_uuid = request.POST.get('device_uuid', "")

    # Check that all require params are sent and are of the right format
    if (auth_token == None or auth_token.strip() == "" or auth_token.find('_') == -1) or (device_uuid == None or device_uuid.strip() == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # get the account id and the device the user is logging in from
    account_id = auth_token.split('_')[1]
    account = get_object_or_404(Account, pk=account_id)

    # Get the device and update its fields. Also empty the auth_token
    device = Device.objects.get(uuid = device_uuid, account_id = account)
    device.last_seen_date = datetime.datetime.now()
    device.ip_address = get_client_ip(request)
    device.auth_token = ""
    device.save()

    response_data = {"status":1}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Register with Facebook
@csrf_exempt
@require_POST
def facebook(request):
    facebook_id = request.POST.get('user_id', "")
    display_name = request.POST.get('name',"")
    email = request.POST.get('email', "")
    device_uuid = request.POST.get('device_uuid', "")

    # Check that all required fields are sent
    if (facebook_id == None or facebook_id.strip() == "") or (device_uuid == None or device_uuid.strip() == "") or (email == None or email.strip() == ""): 
        response_data = {"status":0, "error":"A required parameter was not provided."}
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # Check for a display name and if it is missing attempt to create one from the first and last name
    if display_name == None or display_name.strip() == "":
        first_name = request.POST.get('first_name', "")
        last_name = request.POST.get('last_name', "")
        if (first_name == None or first_name.strip() == "") or (last_name == None or last_name.strip() == ""):
            response_data = {"status":0, "error":"No name was provided."}
            return HttpResponse(json.dumps(response_data), content_type="application/json")
        else:
            display_name = first_name + " " + last_name
    
    # Update or create the account
    account = Account.objects.get_or_create(
        facebook_id=facebook_id,
        defaults= {'display_name': display_name,'email': email,})[0]
    account.display_name = display_name
    account.email = email
    account.save()

    # Register device to the client
    device_register(get_client_ip(request), device_uuid, account)
    response_data = {"status":1}
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Show detail on an account
@csrf_exempt
def detail(request, account_id):
    account = get_object_or_404(Account, pk=account_id)
    devices = Device.objects.filter(account_id=account_id)
    buyer_items = BuyerItem.objects.filter(buyer=account_id)
    items_viewed = buyer_items.count()
    seller_items = Items.objects.filter(seller=account_id)
    total_items = seller_items.count()
    items_sold = Items.objects.filter(seller=account_id, status=Items.SOLD).count()
    context = {
        'account': account,
        'devices': devices,
        'items': buyer_items,
        'selling': seller_items,
        'item_count': total_items,
        'items_sold': items_sold,
        'items_viewed': items_viewed
    }
    print(context)
    return render(request, 'account/detail.html', context)

# Show detail on an account
@csrf_exempt
def dashboard(request):
    registered_users = Account.objects.count()
    active_users = Account.objects.filter(disabled = False).count()
    total_items = Items.objects.count()
    total_sold = Items.objects.filter(status = Items.SOLD).count()
    total_expired = Items.objects.filter(status = Items.EXPIRED).count()
    total_spam = Items.objects.filter(status = Items.SPAM).count()
    total_deleted = Items.objects.filter(status = Items.DELETED).count()
    total_pending = Items.objects.filter(status = Items.PENDING).count()
    
    context = {
        'register_users': registered_users,
        'active_users': active_users,
        'total_items': total_items,
        'total_sold': total_sold,
        'total_expired': total_expired,
        'total_deleted': total_deleted,
        'total_spam': total_spam,
        'total_pending': total_pending
    }
    print(context)
    return render(request, 'account/dashboard.html', context)

## DEVICE STUFF

# Show detail on a device
@csrf_exempt
def device_detail(request, device_id):
    device = get_object_or_404(Device, pk=device_id)
    context = {
        'device': device,
    }
    return render(request, 'account/device_detail.html', context)

# Register a new device
def device_register(ip, uuid, user):
    device = Device.objects.get_or_create(
        uuid = uuid,
        account_id= user,
        defaults={'notifications_enabled': True, })[0]
    device.last_seen_date = datetime.datetime.now()
    device.ip_address = ip
    device.save()
    return device

# Register a new device for notifications
@csrf_exempt
@require_POST
@authenticate
def device_register_push(request):
    device_token = request.POST.get('device_token', "")
    auth_token = request.POST.get('auth_token', "")
    device_uuid = request.POST.get('device_uuid', "")

    # Check that all require params are sent and are of the right format
    if (device_token == None or device_token.strip() == "") or (auth_token == None or auth_token.strip() == "" or auth_token.find('_') == -1) or (device_uuid == None or device_uuid.strip() == ""):
        response_data = { "status":0, "error": "A required parameter was not provided." }
        return HttpResponse(json.dumps(response_data), content_type="application/json")

    # get the account id and the device the user is logging in from
    account_id = auth_token.split('_')[1]
    account = get_object_or_404(Account, pk=account_id)

    # Either get the device or create it if it is a new one 
    device = Device.objects.get_or_create(
        uuid = device_uuid,
        account_id = account,
        defaults={'notifications_enabled': True, })[0]
    device.last_seen_date = datetime.datetime.now()
    device.ip_address = get_client_ip(request)
    device.apns_token = device_token
    device.save()

    response_data = { "status":1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Dispatch a notification to device
@csrf_exempt
def device_notify(request, device_id):
    # TODO: Send an actual message
    device = get_object_or_404(Device, pk=device_id)
    device.send_notification("bob", "default", 42)
    response_data = { "status":1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Dispatch a notification to all devices for that user
@csrf_exempt
def device_notify_all(request, account_id):
    # Get all devices for the account
    devices = Device.objects.filter(account_id=account_id)

    # notify each device
    for device in devices:
        device_notify(request, device.id)
        
    response_data = { "status":1 }
    return HttpResponse(json.dumps(response_data), content_type="application/json")

# Get's the client IP from a request
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

    
