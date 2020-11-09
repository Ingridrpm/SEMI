# -*- coding: utf-8 -*-

import boto3
import botocore
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from flask import Flask, request,jsonify
from flask_cors import CORS, cross_origin
import requests 
import base64
import tempfile
import uuid
import logging
import creds


usuarios = []
id_usuario = 2
estudiantes = []
estudiantes.append({"nombre":"Juana Gonzales", "dpi":"3268562140201", "foto":"estudiante1.jpg"})
estudiantes.append({"nombre":"Carlos Montes", "dpi":"1258465280101", "foto":"estudiante2.jpg"})
estudiantes.append({"nombre":"Tomas Lopez", "dpi":"3658258590304", "foto":"estudiante3.jpg"})
estudiantes.append({"nombre":"Paulina Zepeda", "dpi":"2745810250302", "foto":"estudiante4.jpg"})
estudiantes.append({"nombre":"Gladys Bolaños", "dpi":"2014585200103", "foto":"estudiante5.jpg"})
estudiantes.append({"nombre":"Pablo Villatoro", "dpi":"2015580120203", "foto":"estudiante6.jpg"})
usuarios.append({"id":1, "nombre":"Evaluador", "correo":"evaluador@usac.com", "contra":"123", "grupo":estudiantes})

app = Flask(__name__)
CORS(app)

@app.route('/aspirantes/todos',methods =['GET'])
def aspirantes():
    id = request.args.get('id')
    global usuarios 
    for usuario in usuarios:
        if str(usuario['id']) == id:
            return jsonify(usuario["grupo"])
    return jsonify([])
    
@app.route('/aspirantes/dpi',methods =['GET'])
def dpis():
    id = request.args.get('id')
    global usuarios 
    for usuario in usuarios:
        if str(usuario['id']) == id:
            dpis = []
            for a in usuario["grupo"]:
                dpis.append(a["dpi"])
            return jsonify(dpis)
    return jsonify([]) 
    
@app.route('/aspirantes/uno',methods =['GET'])
def un_aspirante():
    id = request.args.get('id')
    dpi = request.args.get('dpi')
    global usuarios 
    for usuario in usuarios:
        if str(usuario['id']) == id:
            for a in usuario['grupo']:
                if str(dpi) == str(a['dpi']):
                    return jsonify(a)
    return jsonify({}) 

@app.route('/aspirantes/presentes',methods =['GET'])
def presentes():
    id = request.args.get('id')
    foto_grupo = request.args.get('foto_grupo')
    global usuarios 
    for usuario in usuarios:
        if str(usuario["id"]) == id:
            ests = usuario["grupo"]
            presentes = []
            for p in ests:
                presente = comparar(p["foto"],foto_grupo);
                presentes.append({"nombre":p["nombre"], "dpi":p["dpi"], "foto":p["foto"], "presente":presente})
            return jsonify(presentes)
    return jsonify([])
    

@app.route('/s3/upload', methods = ['POST'])
def s3_upload():
    if request.method == 'POST':
        content = request.get_json()
        name = content['name']
        ext = content['ext']
        b64_parts = content['base64'].split(',')
        image_64_encode_str = len(b64_parts) ==2 and b64_parts[1] or b64_parts[0]

        s3_client = boto3.client(
            's3',
            aws_access_key_id=creds.s3['access_key_id'],
            aws_secret_access_key=creds.s3['secret_access_key'],
        )

        BUCKET_NAME = 'front-proyecto1'
        FOLDER_NAME = 'images'
        file_name = '%s.%s' % (name, ext)
        file_path = '%s/%s' % (FOLDER_NAME, file_name)
        image_64_encode = base64.b64decode((image_64_encode_str))
        f = tempfile.TemporaryFile()
        f.write(image_64_encode)
        f.seek(0)

        try:
            response = s3_client.put_object(Body=f, Bucket=BUCKET_NAME, Key=file_path, ACL='public-read')
            logging.info(response)
            return response
        except ClientError as e:
            logging.error(e)
            return e.response
            
@app.route('/usuarios/login',methods =['GET'])
def login():
    correo = request.args.get('correo')
    contra = request.args.get('contra')
    for usuario in usuarios:
        if usuario['correo'] == correo and usuario['contra'] == contra:
            return jsonify({"id":usuario['id']})
    return jsonify({"id":0})
   
@app.route('/usuarios/todos',methods =['GET'])
def users():
    return jsonify(usuarios)
            
@app.route('/usuarios/agregar',methods =['POST'])
def agregar():
    cuerpo = request.get_json()
    nombre = cuerpo['nombre']
    correo = cuerpo['correo']
    contra = cuerpo['contra']
    global usuarios
    global id_usuario
    usuarios.append({"id":id_usuario, "nombre":nombre, "correo":correo, "contra":contra, "grupo":[]})
    id_usuario += 1
    return jsonify({'mensaje':'Agregado correctamente'})
    


@app.route('/rek/compare', methods = ['POST'])
def rek_compare():
    if request.method == 'POST':
        content = request.get_json()
        source_image_name = content['source_image_name']
        target_image_name = content['target_image_name']

        rekognition_client = boto3.client(
            'rekognition',
            aws_access_key_id=creds.rekognition['access_key_id'],
            aws_secret_access_key=creds.rekognition['secret_access_key'],
            region_name=creds.rekognition['region'],
        )

        BUCKET_NAME = 'front-proyecto1'
        FOLDER_NAME = 'images'
        source_image_path = '%s/%s' % (FOLDER_NAME, source_image_name)
        target_image_path = '%s/%s' % (FOLDER_NAME, target_image_name)

        try:
            response = rekognition_client.compare_faces(
                SourceImage={
                    'S3Object': {
                        'Bucket': BUCKET_NAME,
                        'Name': source_image_path,
                    }
                },
                TargetImage={
                    'S3Object': {
                        'Bucket': BUCKET_NAME,
                        'Name': target_image_path,
                    }
                },
                SimilarityThreshold=10,
            )
            print(response)
            if(len(response["FaceMatches"]) != 0):
                return jsonify({"presente":True});
            else:
                return jsonify({"presente":False});
        except ClientError as e:
            logging.error(e)
            return e.response

def comparar(source_image_name, target_image_name):
    rekognition_client = boto3.client(
        'rekognition',
        aws_access_key_id=creds.rekognition['access_key_id'],
        aws_secret_access_key=creds.rekognition['secret_access_key'],
        region_name=creds.rekognition['region'],
    )
    
    BUCKET_NAME = 'front-proyecto1'
    FOLDER_NAME = 'images'
    source_image_path = '%s/%s' % (FOLDER_NAME, source_image_name)
    target_image_path = '%s/%s' % (FOLDER_NAME, target_image_name)
    
    try:
        response = rekognition_client.compare_faces(
            SourceImage={
                'S3Object': {
                    'Bucket': BUCKET_NAME,
                    'Name': source_image_path,
                }
            },
            TargetImage={
                'S3Object': {
                    'Bucket': BUCKET_NAME,
                    'Name': target_image_path,
                }
            },
            SimilarityThreshold=10,
        )
        print(response)
        if(len(response["FaceMatches"]) != 0):
            return True
        else:
            return False
    except ClientError as e:
        return False
        

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True)