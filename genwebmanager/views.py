from genwebmanager.models import DBSession
from genwebmanager.models import MyModel
from genwebmanager.redirections import parseData
from operator import itemgetter
from pyramid.response import Response

from paste.httpheaders import AUTHORIZATION
import json

REDIRECTIONS_PATH = '/var/pyramid/gwmanager/src/genwebmanager/redirections'

def _get_basicauth_credentials(request):
    authorization = AUTHORIZATION(request.environ)
    try:
        authmeth, auth = authorization.split(' ', 1)
    except ValueError: # not enough values to unpack
        return None
    if authmeth.lower() == 'basic':
        try:
            auth = auth.strip().decode('base64')
        except binascii.Error: # can't decode
            return None
        try:
            login, password = auth.split(':', 1)
        except ValueError: # not enough values to unpack
            return None
        return {'login':login, 'password':password}

    return None

def main(request):
    dbsession = DBSession()
    root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    auth = _get_basicauth_credentials(request)
    if auth:
        rsaparam = '-i ~/rsa/%(login)s.rsa' %  (auth)
    else:
        rsaparam = ''
    data = parseData(folderbase=REDIRECTIONS_PATH)

    entorns = [dict(id=int(a),entorn=data['entorns'][a]) for a in data['entorns'].keys()]
    instancies = [data['instancies'][a] for a in data['instancies'].keys()]
    
    returndict = {'root':root, 'project':'Genweb Manager','rsaparam':rsaparam}
    returndict['entorns']=sorted(entorns,key=lambda entorn:entorn['id'])
    returndict['instancies']=sorted(instancies,key=lambda instancia:instancia['title'])
    return returndict
    
    
def export(request):
    dbsession = DBSession()
    root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    auth = _get_basicauth_credentials(request)

    data = parseData(folderbase=REDIRECTIONS_PATH)

    entorns = [dict(id=int(a),entorn=data['entorns'][a]) for a in data['entorns'].keys()]
    instances = [data['instancies'][a] for a in data['instancies'].keys()]

    json_data_list = []
    for ins in instances:
        if len(ins['urls'])>0:
            url = ins['urls'][0]['gwurl'].replace('https','http')
        json_data = dict(url=url,
                         zeoport=ins['zeoport'],
                         debugport=ins['debugport'],
                         mountpoint=ins['mountpoint'],
                         plonesite=ins['plonesite'],
                         title=ins['title'],
                         entorn=ins['entorn'],
                         )
        json_data_list.append(json_data)

    response = Response(json.dumps(json_data_list))
    response.content_type = 'application/json'
    return response

def purge(request):
    dbsession = DBSession()
    root = dbsession.query(MyModel).filter(MyModel.name==u'root').first()
    
    import telnetlib

    telnetport = request.GET.get('telnetport',None)
        
    value = {'result':False}

    if telnetport:
      try:   
          tn = telnetlib.Telnet('sylar.upc.es',int(telnetport))
          tn.write("purge.url .*\n") 
          tn.close()        
          value['result']=True
      except:
          pass

    response = Response(json.dumps(value))
    response.content_type = 'application/json'
    return response