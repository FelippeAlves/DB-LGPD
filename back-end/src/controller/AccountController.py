from flask import Blueprint, Response, request
from bson import json_util
from datetime import datetime
from bson.objectid import ObjectId
from src.model.utils.vault import Commands

from src.model.account import Account as ModelAccount
from src.model.address import Address as ModelAddress
from src.model.utils.crypto import Crypt

bp = Blueprint('account', __name__, url_prefix='/account')

@bp.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':
        crypt_suite = Crypt()
        obj = json_util.loads(crypt_suite.decrypt_front(request.json['data']))
        
        try:
            address = obj.pop("address")
            email = obj.pop("email")
            password = obj.pop("password")

            pkAccount = ObjectId()
            pkAddress = ObjectId()

            crypt_suite.encrypt_init(str(pkAccount))

            account = crypt_suite.encrypt(str(pkAccount), json_util.dumps(obj)).decode('latin-1', 'replace')
            email = crypt_suite.encrypt(str(pkAccount), email).decode('latin-1', 'replace')
            password = crypt_suite.encrypt(str(pkAccount), password).decode('latin-1', 'replace')

            address = crypt_suite.encrypt(str(pkAccount), json_util.dumps(address)).decode('latin-1', 'replace')

            addressObj = ModelAddress()
            addressObj.data = address
            addressObj = addressObj.save()

            accountObj = ModelAccount()
            accountObj.vault_id = pkAccount
            accountObj.email = email
            accountObj.password = password
            accountObj.data = account
            accountObj.address = addressObj
            accountObj.save()

            response = str(accountObj.id)

            command = Commands()
            command.seal()

            return Response(json_util.dumps({"id" : response}), mimetype="application/json", status=200)

        except Exception as error:
            res = {'Message':'Falha na inserção do usuário', 'error': str(error)}
            return Response(json_util.dumps(res), mimetype='application/json', status=500)

    else:
        return Response('{"error":"Method not allowed, use POST"}', mimetype="application/json", status=405)

@bp.route('/login', methods=['POST', 'GET'])
def login():
    
    if request.method == 'POST':
        crypt_suite = Crypt()
        obj = json_util.loads(crypt_suite.decrypt_front(request.json['data']))

        try:
            email = obj.pop("email")
            password = obj.pop("password")

            accountObj = json_util.loads(ModelAccount.objects().only('email', 'password', 'vault_id').to_json())

            for account in accountObj:
                account['email'] = crypt_suite.decrypt(str(account['vault_id']), account['email']).decode('latin-1', 'replace')
                account['password'] = crypt_suite.decrypt(str(account['vault_id']), account['password']).decode('latin-1', 'replace')

            email_list = list(filter(lambda account: account["email"] == email, accountObj))

            if not email_list:
                return Response('{"Message":"Email não encontrado"}', mimetype="application/json", status=404)

            if email_list[0]['password'] != password:
                return Response('{"Message":"Senha invalida"}', mimetype="application/json", status=404)
            
            response = str(email_list[0]['_id'])

            command = Commands()
            command.seal()

            return Response(json_util.dumps({"id" : response}), mimetype="application/json", status=200)

        except Exception as error:
            res = {'Message':'Falha ao logar', 'error': str(error)}
            return Response(json_util.dumps(res), mimetype='application/json', status=500)
    
    else:
        return Response('{"error":"Method not allowed, use POST"}', mimetype="application/json", status=405)

@bp.route('/getUser', methods=['POST', 'GET'])
def get_user():
    
    if request.method == 'POST':
        crypt_suite = Crypt()
        obj = request.json['id']

        try:
            response_object = {}
            account = json_util.loads(ModelAccount.objects.get(id=obj).to_json())
            objAccount = json_util.loads(crypt_suite.decrypt(str(account['vault_id']), account["data"]).decode('latin-1', 'replace'))
            objAccount['email'] = crypt_suite.decrypt(str(account['vault_id']), account["email"]).decode('latin-1', 'replace')

            address = json_util.loads(ModelAddress.objects.get(id=str(account['address'])).to_json())

            response_object['account'] = crypt_suite.encrypt_front(json_util.dumps(objAccount)).decode('latin-1', 'replace')
            response_object['address'] = crypt_suite.encrypt_front(crypt_suite.decrypt(str(account['vault_id']), address["data"]).decode('latin-1', 'replace')).decode('latin-1', 'replace')

            command = Commands()
            command.seal()

            return Response(json_util.dumps(response_object), mimetype="application/json", status=200)

        except Exception as error:
            res = {'Message':'Falha enviar o Id solicitado', 'error': str(error)}
            return Response(json_util.dumps(res), mimetype='application/json', status=500)
    
    else:
        return Response('{"error":"Method not allowed, use POST"}', mimetype="application/json", status=405)

@bp.route('/setUser', methods=['PUT'])
def setUser():
    crypt_suite = Crypt()
    obj = json_util.loads(crypt_suite.decrypt_front(request.json['data']))
    
    try:
        idUser = obj.pop("id")
        address = obj.pop("address")
        email = obj.pop("email")
        password = obj.pop("password")

        accountObj = ModelAccount.objects.get(id=idUser)

        account = crypt_suite.encrypt(str(accountObj["vault_id"]), json_util.dumps(obj)).decode('latin-1', 'replace')
        email = crypt_suite.encrypt(str(accountObj["vault_id"]), email).decode('latin-1', 'replace')
        password = crypt_suite.encrypt(str(accountObj["vault_id"]), password).decode('latin-1', 'replace')
        address = crypt_suite.encrypt(str(accountObj["vault_id"]), json_util.dumps(address)).decode('latin-1', 'replace')

        
        accountObj.email = email
        accountObj.password = password
        accountObj.data = account
        accountObj.updated_at = datetime.utcnow

        addressObj = ModelAddress(id=str(accountObj.address.id))
        addressObj.data = address
        addressObj.updated_at = datetime.utcnow
        
        accountObj.save()
        addressObj.save()

        command = Commands()
        command.seal()

        return Response(json_util.dumps({"Status" : "Success"}), mimetype="application/json", status=200)


    except Exception as error:
        res = {'Message':'Falha na inserção do usuário', 'error': str(error)}
        return Response(json_util.dumps(res), mimetype='application/json', status=500)


@bp.route('/delUser', methods=['POST'])
def del_user():

    crypt_suite = Crypt()
    obj = request.json['id']
 
    try:
        account = ModelAccount.objects.get(id=obj)
    
        account.address.delete()

        account.delete()

        return Response('{"message":"Ok"}', mimetype="application/json", status=200)

    except Exception as error:
        res = {'Message':'Falha enviar o Id solicitado', 'error': str(error)}
        return Response(json_util.dumps(res), mimetype='application/json', status=500) 
