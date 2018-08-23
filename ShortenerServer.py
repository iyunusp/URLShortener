
from gevent.pywsgi import WSGIServer
from flask import Flask, request, abort, Response, jsonify, send_file,redirect
from flaskext.mysql import MySQL

import warnings
import json
import logging
from validators.url import url as check
import re


logger= logging.getLogger(__name__)
#class for line server
class ShortenerServer(object):
    app=Flask(__name__)
    agent=None
    users_inProcess={}
    premium=False
    mysql=MySQL()
    app.config["MYSQL_DATABASE_USER"]="iyunusp"
    app.config["MYSQL_DATABASE_PASSWORD"]="waspeper"
    app.config["MYSQL_DATABASE_DB"]="aea"
    app.config["MYSQL_DATABASE_HOST"]="0.0.0.0"
    mysql.init_app(app)
    #engine=create_engine("mysql://aea:Xd4Y-2qA!7vr@den1.mysql4.gear.host/aea")
    """
    DROP PROCEDURE IF EXISTS proc_shortener;
    DELIMITER //
    create PROCEDURE proc_shortener (
        IN p_shortcut varchar(15),
        IN p_url text
    )
    BEGIN
            IF(SELECT EXISTS (SELECT 1 FROM shortener WHERE shortcut = p_shortcut)) THEN
            SELECT 'Failed';
        ELSE
            INSERT INTO shortener(shortcut,url) VALUES (p_shortcut,p_url);
        END IF;
    END
    //
    DELIMITER ;
    
    """
    "UPDATE `mysql`.`proc` p SET definer = 'iyunusp@%' WHERE definer='aea@%'"
    #utils.configure_file_logging("DEBUG","asd.log")
    def __init__(self):
        import os
        dir=os.path.dirname(os.path.realpath(__file__))
        @self.app.route("/", methods=['GET', 'OPTIONS'])
        def UI():
            """Chatt"""
            return send_file("indexs.html")
        
        @self.app.route("/<shortcut>", methods=['GET', 'OPTIONS'])
        def shortcut(shortcut):
            """Chatt"""
            try:
                conn=self.mysql.connect()
                data=()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM shortener WHERE shortcut = %s LIMIT 1",(shortcut))
                    data=cursor.fetchall()
                url=data[0][1]
                return redirect(url,code=302)
            except:
                return redirect('/',code=302)
            
        @self.app.route("/make/<shortcut>", methods=['GET', 'OPTIONS'])
        def make(shortcut):
            """checking web status"""
            body = request_parameters()
            url=body.pop("url")
            status=self.valid(shortcut,url)
            if not status["success"]:
                return jsonify(status)
            try:
                conn=self.mysql.connect()
                cursor=conn.cursor()
                cursor.callproc("proc_shortener",(shortcut,url))
                data=cursor.fetchall()
                if len(data) == 0:
                    conn.commit()
                    #print(data)
                    status["status"]="shortcut created succesfully"
                else:
                    status["status"]="duplicate shortcut"
                    status["success"]=False
            except:
                status["status"]="Connection Failed"
                status["success"]=False
            return jsonify(status)

        @self.app.route("/image/<path>", methods=['GET', 'OPTIONS'])
        def image(path):
            return send_file(dir+"/image/"+path,mimetype="image/*")
        
        def request_parameters():
            if request.method == 'GET':
                return request.args.to_dict()
            else:
                try:
                    return request.get_json(force=True)
                except ValueError as e:
                    pass
    def valid(self,shortcut,url):
        reg=re.compile(r'^[a-zA-Z0-9]{1,14}$')
        status={"status":"","success":False}
        if len(shortcut) == 0 or len(url)==0:
            status["status"]="all field must be filled"
        elif len(shortcut) > 15:
            status["status"]="must be less than 15 character"
        elif re.match(reg,shortcut) is None:
            status["status"]="shortcut must be alphanumeric"
        elif shortcut == "make":
            status["status"]="can't use reserved path"
        elif check(url) is not True:
            status["status"]="url is invalid"
        else:
            status["success"]=True
        return status
            
        
        
    def startApp(self):
        http_server = WSGIServer(('0.0.0.0', 5005), self.app)
        logger.info("Up and running")
        try:
            http_server.serve_forever()
        except Exception as exc:
            logger.exception(exc)
    
server= ShortenerServer()
server.startApp()

