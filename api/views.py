from django.shortcuts import render
from django.contrib.auth import login, logout, get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response 
from .models import Organisation, CustomUser

# Create your views here.

@api_view(["GET"])
def get_data(request):
    me = {
        "name":"Ace",
        "Stack":"Django"
    }
    return Response(me)


#--------------------------Register User---------------------------------------------
@api_view(["POST"])
def register_user(request) -> Response:
    firstName = request.data.get("firstName")
    lastName = request.data.get("lastName")
    email = request.data.get("email")
    password = request.data.get("password")
    phone = request.data.get("phone")

    if not phone:
        phone = None

    validation_response = validate_reg_form(firstName=firstName, lastName=lastName, email=email, password=password)
    if validation_response is not None:
        return validation_response
    try:
        new_user = CustomUser.objects.create(firstName=firstName, lastName=lastName, email=email, phone=phone)
        userId = new_user.userId
        user_org=Organisation.objects.create(owner=new_user, name=f"{firstName}'s Organisation", description=f"An Organisation created by {lastName} {firstName}")
        new_user.set_password(password)  # Hash the password
    except Exception as e:
        data = {
            "status": "Bad request",
            "message": "Registration unsuccessful",
            "statusCode": 400
        }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    user_org.save()
    new_user.save()
    access_token = AccessToken.for_user(new_user)
    access_token = str(access_token)
    success_json = handleLogRegSuccess(userId=userId,firstName=firstName, lastName=lastName, email=email, registration=True, phone=phone, access_token=access_token )
    return Response(success_json, status=status.HTTP_201_CREATED)



# Validate Registration form 
def validate_reg_form(firstName, lastName, email, password) -> None:
    if not firstName or firstName == "":
        err= handleRegistrationError(field = "firstName", message="Invalid Input")
        return Response(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not lastName or lastName == "":
        err = handleRegistrationError(field = "lastName", message="Invalid Input")
        return Response(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if not email or email == "":
        err = handleRegistrationError(field = "email", message="Invalid Input")
        return Response(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    if CustomUser.objects.filter(email=email).exists():
        err = handleRegistrationError(field = "email", message="Already Exists")
        return Response(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    
    if not password or password == "":
        err = handleRegistrationError(field = "password", message="Invalid Input")
        return Response(err, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    return None
    
    



def handleRegistrationError(**kwargs)->dict:
    field=kwargs["field"]
    message=kwargs["message"]
    error = {"errors": [{"field": field,  "message": message},]}
    return error



def handleLogRegSuccess(**kwargs)->dict:
    reg = kwargs["registration"]
    userId=kwargs["userId"]
    firstName=kwargs["firstName"]
    lastName=kwargs["lastName"]
    email=kwargs["email"]
    phone=kwargs["phone"]
    access_token = kwargs["access_token"]

    message = "Login successful"
    if reg:
        message ="Registration successful"

    data = {
        "status": "success",
        "message": message,
        "data": {
        "accessToken": access_token,
        "user": {
            "userId": userId,
            "firstName": firstName,
                    "lastName": lastName,
                    "email": email,
                    "phone": phone,
            }
        }
    }
    return data




#---------------------------LOGIN------------------------------------------------------------
@api_view(["POST"])
def login_user(request):
    email=request.data.get("email")
    password=request.data.get("password")

    # user = authenticate(request, email, password)

    try:
        user = CustomUser.objects.get(email = email)
        if not user.check_password(password):
            user = None
    except:
        user = None
    if user is None:
        error_json = {
            "status": "Bad request",
            "message": "Authentication failed",
            "statusCode": 401
        }
        return Response(error_json, status=status.HTTP_401_UNAUTHORIZED)

    login(request, user)
    access_token = AccessToken.for_user(user)
    access_token = str(access_token)
    success_json = handleLogRegSuccess(userId=user.userId,firstName=user.firstName, lastName=user.lastName, email=email, registration=False, phone=user.phone, access_token =access_token )
    return Response(success_json, status=status.HTTP_200_OK)

    
def authenticate(request, email, password):
    userModel = get_user_model()
    try:
        user = userModel.objects.get(email=email)
    except userModel.DoesNotExist:
        return None
    
    if user.check_password(password):
        return user
    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user(request, id):
    user = request.user
    if not CustomUser.objects.filter(userId=id).exists():
        data = {
            "status": "Not Found",
            "message": "User not found",
            "statusCode": 404
        }
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    lookup_user = CustomUser.objects.get(userId=id)

    
    U_all_org = Organisation.objects.filter(owner=user) | Organisation.objects.filter(members=user)
    LU_all_org= Organisation.objects.filter(owner=lookup_user) | Organisation.objects.filter(members=lookup_user)
    common_organisations = U_all_org & LU_all_org
    if common_organisations.exists() or id == user.userId:
        data = {
            "userId": lookup_user.userId,
            "firstName": lookup_user.firstName,
			"lastName": lookup_user.lastName,
			"email": lookup_user.email,
			"phone": lookup_user.phone,
        }
        user_response = handle_successful_response(data, message="User Found")
        return Response(user_response)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_organisation(request, orgId):
    user = request.user

    if not Organisation.objects.filter(orgId=orgId).exists():
        data = {
            "status": "Not Found",
            "message": "Organisation not found",
            "statusCode": 404
        }
        return Response(data, status=status.HTTP_404_NOT_FOUND)
    
    org =Organisation.objects.get(orgId=orgId)
    data = {
        "orgId":org.orgId,
        "name":org.name,
        "description": org.description,
    }
    new_response = handle_successful_response(data, message="Organisation Retrieved")
    return Response (new_response, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def get_and_create_org(request):
    user = request.user

    if request.method == "GET":
        all_userRelOrganisations= Organisation.objects.filter(owner=user) | Organisation.objects.filter(members=user)
        
        if not all_userRelOrganisations.exists():
            data =handle_successful_response(message="No Organisation Found")
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        
        list=[{}]
        for org in all_userRelOrganisations:
            data_to_append={
                "orgId": org.orgId,
                "name": org.name,
                "description": org.description,
            }
            list.append(data_to_append)
        main_data = {"organisation":list}

        return Response(main_data, status = status.HTTP_200_OK)
    

    elif request.method == "POST":
        if request.data.get("name") is None or request.data.get("name") == "":
            data = {
                "status": "Bad Request",
                "message": "Client error",
                "statusCode": 400
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        
        name = request.data.get("name")
        description= request.data.get("description")
        new_org=Organisation.objects.create(owner=user, name=name, description=description)
        new_org.save()
        data = {
            "orgId": new_org.orgId,
            "name": name,
            "description":description
        }
        proper_response = handle_successful_response(data=data, message="Organisation created successfully")
        return Response(proper_response, status=status.HTTP_201_CREATED)
        

def handle_successful_response(data:dict ="", message="") -> dict:
    new_json={
        "status": "success",
        "message": message,
        "data": data
    }
    return new_json

@api_view(["POST"])
def add_user_to_org(request, orgId):
    userId = request.data.get("userId")
    user = CustomUser.objects.get(userId=userId)
    org = Organisation.objects.get(orgId=orgId)
    org.members.add(user)
    org.save()
    data = {
        "status": "success",
        "message": "User added to organisation successfully",
    }
    return Response(data, status=status.HTTP_200_OK)