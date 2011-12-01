# -*- coding: utf-8 -*-

import os
import urllib2
import random
import json
import requests

REDIRECTIONS_FOLDER = '.'
https_redirections = {}
VARNISH_TELNET_BASE = 9100
VARNISH_BASE = 9000
HAPROXY_BASE = 10000
ZEOCLIENT_BASE = 11000
DEBUGCLIENT_BASE = 11900
DORSALS = {"1":"Víctor Valdés", "2":"Dani Alves", "3":"Piqué", "4":"Cesc", "5":"Puyol", "6":"Xavi", "7":"David Villa", "8":"A. Iniesta",
           "9":"Bojan", "10":"Messi", "11":"Jeffren", "12": "Unknown", "13":"Pinto", "14":"Mascherano", "15":"Keita", "16":"Sergio" }
SYLARS = {'a':'sylara.upc.es','b':'sylarb.upc.es','c':'sylarc.upc.edu'}

def getPortsByPort(port):
    """
    """
    porti = int(port)
    #Obtenim el numero d'entorn segons si el port que hem passat es de varnish o de zeo
    
    magicnumber = porti < ZEOCLIENT_BASE and porti - VARNISH_BASE or porti - ZEOCLIENT_BASE
    return {'zeoport':str(ZEOCLIENT_BASE+magicnumber), 
            'varnishtelnet':str(VARNISH_TELNET_BASE+magicnumber), 
            'haproxyport':str(HAPROXY_BASE+magicnumber), 
            'entorn':str(magicnumber), 
	    'debugport':str(DEBUGCLIENT_BASE+magicnumber),
            'varnishport':str(VARNISH_BASE+magicnumber)}        

def parseNginxRedirections(fi):
    """
    """
    fif = open(fi)
    text = fif.read()
    data = text.split('\n')
    rewrites = [a.lstrip() for a in data if a.lstrip().startswith('rewrite') and 'VirtualHostBase' in a]
    redirects = []
    for rewrite in rewrites:
        #print "  --> Processing %s" % (rewrite)
        rw_parts = rewrite.split()
        vh = rw_parts[2]
        re = rw_parts[1]
        parts = vh.split('/')
        
        if len(parts)>7:

            proxy_pass_start = text.find('proxy_pass',text.find(rewrite))
            proxy_pass_end = text.find(';',proxy_pass_start)
            port = text[proxy_pass_start:proxy_pass_end].split(':')[-1]
            magicnumber = int(port)-9000
            if magicnumber>0:
                protocol = parts[2]
                domain = parts[3].split(':')[0]
                mountpoint = parts[4]
                plonesite = parts[5]

                if re.startswith('^'):
                    base_path = re.split('^')[1].split('(')[0]
                    if base_path:
                       if base_path[0]!='/':
                           base_path = '/'+base_path
                    else:
                       base_path = ''
                else:
                    base_path = '/'+parts[8]

                
                if 'VirtualHostRoot' in plonesite :
                    pass
                else:
    #                protocols = {}
    #                protocols[protocol] = dict(file = fi,rule = rewrite.lstrip())
                    url = '%s://%s%s' % (protocol,domain,base_path)
                    redirection_data = dict(varnishport = port,
                                        haproxyport = str(HAPROXY_BASE+magicnumber),
                                        varnishtelnet = str(VARNISH_TELNET_BASE+magicnumber),
                                        zeoport = str(ZEOCLIENT_BASE+magicnumber),
                                        debugport = str(DEBUGCLIENT_BASE+magicnumber),
                                        gwurl = url.rstrip('/'),
                                        entorn = magicnumber,                                    
                                        mountpoint = mountpoint,
                                        plonesite = plonesite,
                                        file = fi,
    #                                    protocols = protocols
                                         )
                    redirects.append(redirection_data)
    fif.close()
    return redirects



def parseApacheRedirections(fi):
    """
    """
    fif = open(fi)
    text = fif.read()
    data = text.split('\n')


    rewrites = []
    for rd in data:
        stripped = rd.lstrip()
        if rd.startswith('RewriteRule'):

            if 'VirtualHostBase' in rd:
                rewrites.append(stripped)
            else:
                # Buscar rewriterules de redireccio http-https             
                splitted = rd.split()
                if 'login_form' not in rd and 'https' in splitted[2] and '$1' in splitted[2]:
                    gwurl = splitted[2].split('//')[-1].replace('$1','').rstrip('/')
                    pt = dict(file = fi,rule = stripped)                    
                    https_redirections[gwurl] = pt
        
    rewrites = [a.lstrip() for a in data if a.lstrip().startswith('RewriteRule') and 'VirtualHostBase' in a]
    
    
    redirects = []
    for rewrite in rewrites:
        rw_parts = rewrite.split()
        vh = rw_parts[2].strip('$1')
        re = rw_parts[1]
        parts = vh.split('/')
        
        if len(parts)>7:
            port = parts[2].split(':')[1]
            magicnumber = int(port)-9000
            if magicnumber>0:
                
                protocol = parts[4]
                domain = parts[5].split(':')[0]
                mountpoint = parts[6]
                plonesite = parts[7]

                if re.startswith('^'):
                    base_path = re.split('^')[1].split('(')[0]
                    if base_path:
                       if base_path[0]!='/':
                           base_path = '/'+base_path
                    else:
                       base_path = ''
                else:
                    base_path = '/'+parts[8]
                base_path.rstrip('/')
                
                if 'VirtualHostRoot' in plonesite :
                    pass
                else:
    #                protocols = {}
    #                protocols[protocol] = dict(file = fi,rule = rewrite.lstrip())
                    url = '%s://%s%s' % (protocol,domain,base_path)
                    redirection_data = dict(varnishport = port,
                                        haproxyport = str(HAPROXY_BASE+magicnumber),
                                        varnishtelnet = str(VARNISH_TELNET_BASE+magicnumber),
                                        zeoport = str(ZEOCLIENT_BASE+magicnumber),
                                        debugport = str(DEBUGCLIENT_BASE+magicnumber),
                                        entorn = magicnumber,
                                        gwurl = url.rstrip('/'),
                                        mountpoint = mountpoint,
                                        plonesite = plonesite,
                                        file = fi,
    #                                    protocols = protocols
                                         )
                    redirects.append(redirection_data)
    fif.close()
    return redirects


def addToRedirections(redirections,redirection):
    """
    """
    if redirection['gwurl'] in redirections.keys():
        print "ALERTA !!!! Redireccio duplicada !!! %s" % (redirection['gwurl'])

    redirections[redirection['gwurl']]= redirection
    
#    protocol,gw = redirection['gwurl'].split('://')
#      item_protocols = redirection.get(protocol,redirection['protocols'])        
#      redirections[gw]['protocols'].update(item_protocols)      
#    else:
#      redirections[gw]=redirection
#      redirections[gw]['gwurl']=gw
      
def getInstanceInfo(instance):
    """
    """
    sl = SYLARS[chr(random.randrange(97,100))]
    print 'Requesting %s:%s Information' % (sl,instance) 
    stats_url = 'http://%s:%s/gwc_stats_info' % (sl,instance)
    req = requests.get(stats_url,auth=('admin','tzmLidT8'))
    json_stats = req.content
    #temporal fins que recataloguem                
    json_stats = json_stats.replace('"size": ,\n','')
    return json.loads(json_stats)

def parseData(folderbase='redirections'): 

    REDIRECTIONS_FOLDER = folderbase
    redirections = {}
    instances = {}
    entorns = {}
    failed = {}
    redirections_folders= ['%s/%s' % (REDIRECTIONS_FOLDER,a) for a in os.listdir(REDIRECTIONS_FOLDER) if os.path.isdir('%s/%s' % (REDIRECTIONS_FOLDER,a))]
    for folder in redirections_folders:
        files = ['%s/%s' % (folder,a) for a in os.listdir(folder) if os.path.isfile('%s/%s' % (folder,a))]
        for fi in files:
            #print "* Opening %s" % fi
            if 'apache' in fi:
                apacheredirections = parseApacheRedirections(fi)
                for ar in apacheredirections:
                    addToRedirections(redirections,ar)
            if 'nginx' in fi:
                nginxredirections = parseNginxRedirections(fi)
                for ar in nginxredirections:
                    addToRedirections(redirections,ar)


    #for a in redirections.keys():
    #    if 'http' not in redirections[a]['protocols'].keys():
    #        if redirections[a]['gwurl'] in https_redirections.keys():
    #            redirections[a]['protocols']['http']=https_redirections[redirections[a]['gwurl']]
         

    #Agafar la configuracio de sylara per saber a quin backend esta la instància
    config = urllib2.urlopen('http://mebsuta.upc.es/config/sylara.upc.es').read()
    backends_by_port = dict([(a[2],a[3]) for a in [a.split() for a in config.split('\n') if a]])
         
    #agrupar les urls trobades a les redireccions per instances genweb identificades per port/mountpoint/plonesite            
    savedtitles = False
    if os.path.exists(REDIRECTIONS_FOLDER+'/instance_titles'):    
        savedtitles=True
        instancetitles = dict([a.split('||') for a in open(REDIRECTIONS_FOLDER+'/instance_titles').read().split('\n')])
    for redir in redirections.keys():
        key = '%(zeoport)s/%(mountpoint)s/%(plonesite)s' % redirections[redir]
        data = instances.get(key,{})
        urls = list(data.get('urls',[]))                
        urls.append(redirections[redir])
        data['urls']=[{'gwurl':a['gwurl'],'file':a['file']} for a in urls]                        
        if not 'zeoport' in data.keys():
            # El primer cop que ens trobem una url d'una instancia, omplim les dades daquesta
            # La resta de vegades ja les tindrem
            data['zeoport']=urls[0]['zeoport']            
            data['debugport']=urls[0]['debugport']
            data['varnishtelnet']=urls[0]['varnishtelnet']
            data['varnishport']=urls[0]['varnishport']
            data['haproxyport']=urls[0]['haproxyport']
            data['mountpoint']=urls[0]['mountpoint']
            data['plonesite']=urls[0]['plonesite']
            data['backend']=backends_by_port[data['zeoport']]
            data['entorn']=str(urls[0]['entorn'])
            data['dorsal']=DORSALS[data['entorn']].decode('utf-8')

        try:
            if savedtitles:
                data['title']=instancetitles[key].decode('utf-8')
            else:
                instance_info = getInstanceInfo(key)
                data['title']= instance_info['title']
        except:
            data['title']= 'CANNOT CONNECT TO GET TITLE'
            failedredir = failed.setdefault(key,[])
            failedredir.append(dict(redir=redir,file=redirections[redir]['file']))

        instances[key]=data

    if not os.path.exists(REDIRECTIONS_FOLDER+'/instance_info'):
        instancetitles = {}
        for ikey in instances.keys():
            instance = instances[ikey]
            instancetitles[ikey]=instance['title']
        open(REDIRECTIONS_FOLDER+'/instance_titles','w').write('\n'.join(['%s||%s' % (a,instancetitles[a]) for a in instances.keys()]))


    for ikey in instances.keys():
        instancia = instances[ikey]
        entorn = entorns.get(instancia['entorn'],{})
        if entorn == {}:
            entorn['instancies']=[]
            entorn['zeoport']=instancia['zeoport']
            entorn['debugport']=instancia['debugport']
            entorn['varnishtelnet']=instancia['varnishtelnet']
            entorn['varnishport']=instancia['varnishport']
            entorn['haproxyport']=instancia['haproxyport']
            entorn['backend']=instancia['backend']

        newinstancia = dict(title=instancia['title'],urls=[a['gwurl'] for a in instancia['urls']],plonesite=instancia['plonesite'],mountpoint=instancia['mountpoint'])    
        entorn['instancies'].append(newinstancia)  
        entorns[instancia['entorn']]=entorn

       
    #Fer una llista dels entorns reals que hi ha
    known_instances = []

    for key in entorns.keys():
        entorn = entorns[key]
        entorn['count']=len(entorn['instancies'])

    for entorn in entorns.keys():
        port = str(11000+int(entorn))
        host = 'sylarc.upc.edu'
        url = 'http://%s:%s/@@listPloneSites' % (host,port)
        getSites = requests.get(url)
        json_sites = json.loads(getSites.content)
        this_instances = ['%s/%s' % (port,a) for a in json_sites]
        known_instances+=this_instances

    known_set = set(known_instances) 
    redir_set = set(instances.keys())

    instancies_que_no_tenim_redireccio = known_set - redir_set
    instancies_que_tenen_redireccio_sense_genweb = redir_set - known_set

    print '\n'
    print "Les seguent instàncies existeixen en el seu entorn corresponent, però no tenim cap redirecció que apunti a elles:"
    print "================================================================================================================="
    for i in instancies_que_no_tenim_redireccio:
        print 'http://sylarc.upc.edu:%s' % (i)

    print '\n'
    print "Les següents instàncies NO EXISTEIXEN, però tenen redireccions que hi apunten"
    print "================================================================================================================="    
    for i in instancies_que_tenen_redireccio_sense_genweb:
        print 'http://sylarc.upc.edu:%s' % (i)

    #Esborrem de la llista bona d'instàncies les que no tenen un genweb existent:
    for xunga in instancies_que_tenen_redireccio_sense_genweb:
        del instances[xunga]

    #Afegir a la llista bona d'instàncies les que no tenim la url, pero si que hi ha genweb
    for bona in instancies_que_no_tenim_redireccio:
        try:
            info = getInstanceInfo(bona)
        except:
            print '%s semblava bona pero no ho es' % bona
        else:
            port,mountpoint,plonesite = bona.split('/')
            ports = getPortsByPort(port)
            bonadata = {'title':info['title'], 
                        'urls':[], 
                        'plonesite':plonesite, 
                        'mountpoint':mountpoint, 
                        'dorsal':DORSALS[ports['entorn']], 
                        'backend':backends_by_port[port]}
            bonadata.update(ports)
            instances[bona]=bonadata
    



            
    return dict(entorns = entorns, instancies = instances, failed= failed)
