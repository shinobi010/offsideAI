import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:alexsander123@localhost/offsideAI'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'uploads'
