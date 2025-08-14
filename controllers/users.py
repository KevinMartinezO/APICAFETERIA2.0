import os
import logging
import firebase_admin
import requests
import json
import base64
from fastapi import HTTPException
from firebase_admin import credentials, auth as firebase_auth

from models.users import User
from models.login import Login

from utils.security import create_jwt_token
from utils.mongodb import get_collection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_firebase():
    if firebase_admin._apps:
        return

    try:
        firebase_creds_base64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")

        if firebase_creds_base64:
            firebase_creds_json = base64.b64decode(firebase_creds_base64).decode('utf-8')
            firebase_creds = json.loads(firebase_creds_json)
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with environment variable credentials")
        else:
            # Fallback to local file (for local development)
            cred = credentials.Certificate("secrets/dulceria-secret.json")
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with JSON file")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        raise HTTPException(status_code=500, detail=f"Firebase configuration error: {str(e)}")

initialize_firebase()

async def create_user( user: User ) -> User:

    user_record = {}
    try:
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password
        )
    except Exception as e:
        logger.warning( e )
        raise HTTPException(
            status_code=400,
            detail="Error al registrar usuario en firebase"
        )

    try:
        coll = get_collection("users")

        # Aunque se manden en el payload igual los excluimos ya que sabes el 
        # state inicial cuando se crea el usuario.

        new_user = User(
            name=user.name,
            lastname=user.lastname,
            email=user.email,
            password=user.password
        )

        user_dict = new_user.model_dump(exclude={"id", "password"})
        inserted = coll.insert_one(user_dict)
        new_user.id = str(inserted.inserted_id)
        new_user.password = "*********"  # Mask the password in the response
        return new_user

    except Exception as e:
        firebase_auth.delete_user(user_record.uid)
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


async def login(user: Login) -> dict:
    api_key = os.getenv("FIREBASE_API_KEY")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {
        "email": user.email,
        "password": user.password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)
    response_data = response.json()

    if "error" in response_data:
        raise HTTPException(
            status_code=400,
            detail="Error al autenticar usuario"
        )

    coll = get_collection("users")
    user_info = coll.find_one({ "email": user.email })

    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado en la base de datos"
        )

    return {
        "message": "Usuario Autenticado correctamente",
        "idToken": create_jwt_token(
            user_info["name"],
            user_info["lastname"],
            user_info["email"],
            user_info["active"],
            user_info["admin"],
            str(user_info["_id"])
        )
    }