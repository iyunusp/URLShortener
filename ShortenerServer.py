
from gevent.pywsgi import WSGIServer
from flask import Flask, request, abort, Response, jsonify, send_file,redirect,url_for
from flaskext.mysql import MySQL

import warnings
import json
import logging
from validators.url import url as check
import re


logger= logging.getLogger(__name__)
class ShortenerServer(object):
    """Class For URL Shortcut Maker"""
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
    """
    --store procedure for check and create rather the shotcut is already used or not 
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
    def __init__(self):
        import os
        dir=os.path.dirname(os.path.realpath(__file__))
        @self.app.route("/", methods=['GET', 'OPTIONS'])
        def UI():
            """Web Interface for sCreating new URL Shortcut"""
            return send_file("indexs.html")
        
        @self.app.route("/<shortcut>", methods=['GET', 'OPTIONS'])
        def shortcut(shortcut):
            """Chatt"""
            try:
                conn=self.mysql.connect()
                data=()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT url FROM shortener WHERE shortcut = %s LIMIT 1",(shortcut))
                    data=cursor.fetchall()
                url=data[0][0]
                return redirect(url,code=302)
            except:
                return redirect(url_for('UI'),code=302)
            
        @self.app.route("/make/<shortcut>", methods=['POST', 'OPTIONS'])
        def make(shortcut):
            """API for creating new URL Shortcut"""
            body = request_parameters()
            print(body)
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
                    status["status"]="shortcut created succesfully"
                else:
                    status["status"]="shortcut already in used"
                    status["success"]=False
            except:
                status["status"]="Connection Failed"
                status["success"]=False
            return jsonify(status)

        @self.app.route("/image/<path>", methods=['GET', 'OPTIONS'])
        def image(path):
            """Image API for getting Image that stored in image folder"""
            return send_file(dir+"/image/"+path,mimetype="image/*")
        
        def request_parameters():
            availableMethod=['POST','GET']
            if request.method in availableMethod:
                return request.args.to_dict()
            else:
                try:
                    return request.get_json(force=True)
                except ValueError as e:
                    pass
    def valid(self,shortcut,url):
        "form validator"
        reg=re.compile(r'^[a-zA-Z0-9]{1,14}$')
        status={"status":"","success":False}
        if len(shortcut) == 0 or len(url)==0:
            status["status"]="all field must be filled"
        elif len(shortcut) > 15:
            status["status"]="must be less than 15 character"
        elif re.match(reg,shortcut) is None:
            status["status"]="shortcut must be alphanumeric"
        elif shortcut == "make":
            status["status"]="shortcut already in used"
        elif check(url) is not True:
            status["status"]="url is invalid"
        else:
            status["success"]=True
        return status
            
        
        
    def startApp(self):
        """Start the Server using WSGI"""
        http_server = WSGIServer(('0.0.0.0', 5005), self.app)
        logger.info("Up and running")
        try:
            http_server.serve_forever()
        except Exception as exc:
            logger.exception(exc)
    
server= ShortenerServer()
server.startApp()

