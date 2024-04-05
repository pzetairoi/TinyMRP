import os
basedir = os.path.abspath(os.path.dirname(__file__))

###################################
########## MRP config #############
###################################
import pandas as pd   #Dataframe libraries


class TinyConfig:
    
###Function for loading the tinymrp config file from excel, 
## to be integrated in a more elegant way
    def loadconfiguration(filein='TinyMRP_conf.xlsm'):

            excelfile=pd.ExcelFile(filein)
            PROCESS_CONF=excelfile.parse('process').fillna('')
            PROPERTY_CONF=excelfile.parse('property').fillna('')
            VARIABLES_CONF=excelfile.parse('variables').fillna('')
            processfields_conf=excelfile.parse('processfields').fillna('')

            FILES_CONF=excelfile.parse('files').fillna('')
            FILES_CONF=FILES_CONF.set_index('filetype').to_dict('index')



            
            PROCESS_CONF=PROCESS_CONF.set_index('process').to_dict('index')
            PROPERTY_CONF=PROPERTY_CONF.set_index('property').to_dict('index')
            VARIABLES_CONF=VARIABLES_CONF.set_index('variable').to_dict('index')
            processfields_conf=processfields_conf.set_index('process').to_dict('index')

            fieldlist=[]
            fieldorder=[]
            
            for process in PROCESS_CONF.keys():
                fieldlist=[]
                fieldorder=[]
                for property in PROPERTY_CONF.keys():
                    try:
                        if str(processfields_conf[process][property]).isalnum() and str(processfields_conf[process][property])!='nan':
                            #print("value",processfields_conf[process][property] )
                            fieldlist.append({'prop':property,'order':str(processfields_conf[process][property])})
                            fieldorder.append(str(processfields_conf[process][property]))
                    except:
                        pass
                        # #print("Issue with " , process , property)
                
                #Range the list so the print out is ordered
                def myFunc(e):
                    return e['order']

                try:
                    fieldlist.sort(key=myFunc)
                except:
                    pass
                    # #print("Couldnt sort ",process)
                
                fieldlist= [x['prop'] for x in fieldlist]

                try:
                    PROCESS_CONF[process]['fields']=fieldlist
                    #PROCESS_CONF[process]['fieldsorder']=fieldorder
                except:
                    pass
                    # #print("List issue with " , process , property)
                #print(process,fieldlist)

            #print(PROCESS_CONF)
            return [PROCESS_CONF,PROPERTY_CONF,VARIABLES_CONF,FILES_CONF]


    
    #MRP Configuration strings
    DELIVERABLES=["dxf","edr","edr_d","jpg","jpg_d","pdf","png","png_d","step"]
    MAINCOLS=["partnumber","revision","description","material","process","process2","process3","finish"]
    REFCOLS=["approved","totalqty","mass","thickness", 'category','oem','oem_partnumber',"datasheet","link","classified"]

    lowercase_properties=["process","process2","process3","finish","treatment"]
    LOWERCASE_PROPERTIES=["process","process2","process3","finish","treatment"]
    HARDWARE_FOLDER=['toolbox','browser','fasteners']   

    
    ########## IMPORTANT ENVIROMENT VARIABLES TO LOAD FROM THE EXCEL FILE
    PROCESS_CONF,PROPERTY_CONF, VARIABLES_CONF,FILES_CONF = loadconfiguration()


    main_folder=VARIABLES_CONF['tinymrp']['value']
    FOLDEROUT=VARIABLES_CONF['folderout']['value']
    DELIVERABLES_FOLDER=VARIABLES_CONF['deliverables_folder']['value']
    FILESERVER_PATH=VARIABLES_CONF['fileserver_path']['value']
    WEBFILESERVER=VARIABLES_CONF['webfileserver']['value']
    DATASHEET_FOLDER=VARIABLES_CONF['datasheet_folder']['value']
    WEBSERVER=VARIABLES_CONF['webserver']['value']

    
    #Dictionary to store all the fileserver related values
    DELIVERABLES={}
    DELIVERABLES_PATH=(FILESERVER_PATH+"/"+DELIVERABLES_FOLDER).replace("""//""","/")

    for filetype in FILES_CONF.keys():
        DELIVERABLES[filetype]={}
        DELIVERABLES[filetype]['path']=(DELIVERABLES_PATH+"/"+FILES_CONF[filetype]['folder']+"/").replace("""//""","/")
        DELIVERABLES[filetype]['list']=FILES_CONF[filetype]['list']
        DELIVERABLES[filetype]['field']=FILES_CONF[filetype]['field']
        filemod=str(FILES_CONF[filetype]['filemod'])
        if filemod!='nan' and filemod!="": 
            DELIVERABLES[filetype]['filemod']=filemod
        else:
            DELIVERABLES[filetype]['filemod']=""
        DELIVERABLES[filetype]['extension']=[]
        for i in range(0,6):
            reffield="extension"+str(i)
            if str(FILES_CONF[filetype][reffield])!='nan':
                DELIVERABLES[filetype]['extension'].append(FILES_CONF[filetype][reffield])

    
    #Fileset to be incloudedc in all the datatables export filelist, it is repeated
    #witht the code above, the whole config needs a clean up
    fileset=[]
    allfiles=[]
    for filetype in FILES_CONF.keys():
        refdict=FILES_CONF[filetype]
        if FILES_CONF[filetype]['list']=='yes':            
            refdict['filetype']=filetype
            fileset.append(refdict)
        allfiles.append(refdict)


    ALLFILES=allfiles
    FILESET=fileset







    # Process releated configuration icons, images , colours etc
    # #print(PROCESS_CONF.keys())
    # PROCESS_DESCRIPTION=[ [x,PROCESS_CONF[x]['icon'], PROCESS_CONF[x]['color']] for x in PROCESS_CONF.keys()]
    PROCESS_DESCRIPTION=[]

    for x in PROCESS_CONF.keys():
        PROCESS_DESCRIPTION.append([x,PROCESS_CONF[x]['icon'], PROCESS_CONF[x]['color']] )

    
    processes=[]
    icons=[]
    colors=[]

    for process in PROCESS_CONF.keys():
        processes.append(process)
        icons.append(PROCESS_CONF[process]['icon'])
        colors.append(PROCESS_CONF[process]['color'])

    PROCESS_LEGEND=[ {'process':process,'icon':'images/'+icon,'color':color} for  (process,icon,color) in zip(processes,icons,colors) ]
    PIC_LOCATION = FILESERVER_PATH+ FILESERVER_PATH+"/pic"
    REPORTS_PATH=FOLDEROUT


    #TEMPLATES_AUTO_RELOAD = True
    fileserver=WEBFILESERVER
    UPLOAD_PATH='upload'

    #AWS S3 bucket for remote files
    BUCKET= "tinymrp-test"
    FLASKS3_BUCKET_NAME= BUCKET


class Config(TinyConfig):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    
    #Email configuration

    # #Dummy python email
    # MAIL_SERVER = 'localhost'
    # MAIL_PORT = 25
    # MAIL_USE_TLS = False
    # MAIL_USERNAME = None
    # MAIL_PASSWORD = None


    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    
    #For external mail server
    # MAIL_SERVER = os.environ.get('MAIL_SERVER', 'mail.privateemail.com')
    MAIL_SERVER = 'mail.privateemail.com'
    MAIL_PORT = int('587')
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
       ['true', 'on', '1']
    MAIL_USERNAME = "admin@tinymrp.com"
    MAIL_PASSWORD ="Tespro"
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    FLASKY_MAIL_SUBJECT_PREFIX = '[TinyMRP]'
    FLASKY_MAIL_SENDER = 'TinyMRP NO-REPLY <admin@tinymrp.com>'
    FLASKY_ADMIN = 'hola <fcoquesada@gmail.com>'
    SSL_REDIRECT = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_POSTS_PER_PAGE = 20
    FLASKY_FOLLOWERS_PER_PAGE = 50
    FLASKY_COMMENTS_PER_PAGE = 30
    FLASKY_SLOW_DB_QUERY_TIME = 0.5

    

    
    @staticmethod
    def init_app(app):
        pass

    
class DevelopmentConfig(Config):
    #print("development config")
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # email errors to the administrators
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.FLASKY_MAIL_SENDER,
            toaddrs=[cls.FLASKY_ADMIN],
            subject=cls.FLASKY_MAIL_SUBJECT_PREFIX + ' Application Error',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False

    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # handle reverse proxy server headers
        try:
            from werkzeug.middleware.proxy_fix import ProxyFix
        except ImportError:
            from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class DockerConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to stderr
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)


class UnixConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # log to syslog
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.INFO)
        app.logger.addHandler(syslog_handler)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'docker': DockerConfig,
    'unix': UnixConfig,
    'tinymrp':TinyConfig,

    'default': DevelopmentConfig
}


