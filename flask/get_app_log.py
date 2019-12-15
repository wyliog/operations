# _*_ coding:utf-8 _*_
from flask import Flask, flash, request, redirect, url_for, json
from werkzeug.utils import secure_filename
import logging, jwt, datetime, os

# from waitress import serve

# 日志过滤
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(128)
# 文件过滤
ALLOWED_EXTENSIONS = {'txt', 'py', 'log', 'conf'}
SECRECT_KEY = 'fanolabs'
# 默认账号密码

username = os.environ.get("username") or "sTlU81+TUluuCRun"
password = os.environ.get("password") or "msRBDafz18bNnuot"
userinfo = {'username': username, 'password': password}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 解密
def jwt_decoding(token):
    decoded = None
    try:
        decoded = jwt.decode(token, SECRECT_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        decoded = {"error_msg": "Token expired !"}
    except Exception:
        decoded = {"error_msg": "Authorization Failure!"}
    return decoded


# 加密
@app.route('/auth', methods=['GET', 'POST'])
def jwt_encoding():
    datetime_int = datetime.datetime.utcnow() + datetime.timedelta(seconds=1200)
    userinfo = request.get_json(force=True)
    data = {
        'exp': datetime_int,
        'userinfo': userinfo
    }
    encoded = jwt.encode(data, SECRECT_KEY, algorithm='HS256')
    return encoded


@app.route('/uploadfile', methods=['POST'])
def upload_log():
    try:
        ret = False
        auth = json.loads(json.dumps({k: request.headers[k] for k in request.headers.keys()}))['Authorization']
        if jwt_decoding(auth)['userinfo']['username'] == username and \
                jwt_decoding(auth)['userinfo']['password'] == password:
            ret = True
        else:
            ret = False

        if request.files and ret:
            try:
                file = request.files['file']
                if file.filename == '':
                    return 'No selected file'
                    # flash('No selected file')
                    # return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(filename)
                    with open(filename, encoding='utf-8', errors='ignore') as f:
                        print(f.readlines())
                        # for i in f.readlines():
                        #     print(i)
                    os.remove(filename)
                    return 'upload log file success!'
                else:
                    return 'File types are not supported!'
            except KeyError as e:
                print(repr(e))
                return 'No file part'
                # flash('No file part')
                # return redirect(request.url)
        elif ret:
            print(request.get_data().decode())
            return "upload body success"
        else:
            return 'Authorization Failure!'
    except KeyError as e:
        return 'Authorization Failure!'


if __name__ == '__main__':
    # serve(app,host='0.0.0.0',port=8080)
    app.run(debug=False, port=8080, host='0.0.0.0')
