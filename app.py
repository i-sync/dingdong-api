import os
import re
import json
import time
from logger import logger
from utils import json2obj


from flask_httpauth import HTTPBasicAuth
from flask import Flask, request, jsonify, make_response, abort

#CONSTANT
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MUSIC_PATH = '/mnt/sda1/ximalaya'
MUSIC_INDEX_PATH = os.path.join(BASE_PATH, 'index.json')
HTTP_PREFFIX = 'http://xxx.com'


index_content = []
app = Flask(__name__)
auth = HTTPBasicAuth()

@app.route('/')
@auth.login_required
def index():
    return "Error!"

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@auth.get_password
def get_password(username):
    if username == 'test':
        return 'python'
    return None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

"""
Index Section
"""

def get_index():
    # check index content, if has index , return.
    if index_content:
        return index_content
    
    # check index content path, if not exists , return None
    if not os.path.exists(MUSIC_INDEX_PATH):
        return None
    
    with open(MUSIC_INDEX_PATH, 'a+', encoding='utf-8') as f:
        index_content = json.load(f)
    
    return index_content

def update_index():
    # remove before rebuild
    if os.path.exists(MUSIC_INDEX_PATH):
        os.remove(MUSIC_INDEX_PATH)

    res = []
    for root, dirs, files in os.walk(MUSIC_PATH):
        #print(root)
        if len(dirs):
            continue
        album_name = root.split('/')[-1]
        keys = [key for key in re.split(r'[^\w\u4e00-\u9fa5]+', album_name) if key]
        res.append({'name': ''.join(keys), 'origin_name': album_name, 'keys':keys, 'path': root, 'count':len(files), 'list': sorted(files)})
        logger.info({'name': ''.join(keys), 'origin_name': album_name, 'keys':keys, 'path': root, 'count':len(files)})
    
    index_content = res
    if len(res):
        with open(MUSIC_INDEX_PATH, 'w+', encoding='utf-8') as f:
            f.write(json.dumps(res, ensure_ascii=False))

@app.route('/api/miaolaoshi', methods=['POST'])
@auth.login_required
def miaolaoshi():
    #print(request.json)
    if not request.json:
        abort(404)

    logger.info(json.dumps(request.json, ensure_ascii=False))

    res = {}
    res['versionid'] = '1.0'
    res['sequence'] = request.json['sequence']
    respose_body(request.json, res)
    res['timestamp'] = int(round(time.time() * 1000))

    return jsonify(request.json)


def respose_body(req, res):    
    status =  req['status'] if 'status' in req else None
    if status == 'LAUNCH':
        res['is_end'] = False
        #body['need_slot'] = ''
        res['directive'] = {'directive_items': [{'type': '1', 'content': '你好， 你可以对我说播放冰雪奇缘'}] }
        
    elif status == 'INTENT':
        res['is_end'] = False
        song_name = req['slots']['songName']
        res['directive'] = {'directive_items': [{'type': '1', 'content': f'{song_name}'}, {'type': '2', 'content': 'http://a1.xpath.org/%E5%86%B0%E9%9B%AA%E5%A5%87%E7%BC%98/01.%E5%A4%B1%E8%AF%AF%E7%9A%84%E9%AD%94%E6%B3%95.mp3'}] }
        
    elif status == 'END':
        res['is_end'] = True
        res['directive'] = {'directive_items': [{'type': '1', 'content': '再见'}] }
        
    else: #NOTICE        
        res['is_end'] = False        
        res['directive'] = {'directive_items': [{'type': '1', 'content': '哈哈'}] }
        

if __name__ == '__main__':
    app.run(debug=True)