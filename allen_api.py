from flask import Flask, render_template, redirect, request, jsonify
from squad.demo_prepro import prepro
from basic.demo_cli import Demo
import json
from flask_cors import CORS
import urllib
from urllib.parse import quote

app = Flask(__name__)
CORS(app)

# Instantiate demo from basic.demo_cli
demo = Demo()

@app.route('/allen', methods=['GET'])
def allen():
    # What is the user ID of the person TO WHOM we are asking question?
    # This will effect document retrieval.
    respondent_id = request.args.get('id', default = 7606, type = int)

    query = request.args.get('query', default = "What is SocialCam?", type = str) 

    doc_url = "https://molly.com/q?q="+quote(query,safe = '')+"&id="+str(respondent_id)
    with urllib.request.urlopen(doc_url) as url:
            molly_data = json.loads(url.read().decode())

    molly_texts = []
    molly_ids = []
    ids_list = []
    for data_source in molly_data:
        if data_source == 'blog':
            for i, post in enumerate(molly_data[data_source], start = 0):
                molly_data[data_source][i]['span'] = getAnswer(post.get('content'), query)
        elif data_source == 'answer':
            for j, response in enumerate(molly_data[data_source]):
                molly_data[data_source][j]['span'] = getAnswer(response.get('comments'), query)
        elif data_source == 'twitter':
            for k, tweet in enumerate(molly_data[data_source]):
                molly_data[data_source][k]['span'] = getAnswer(tweet.get('text'), query)

    return jsonify(molly_data)

def getAnswer(paragraph, question):
    pq_prepro = prepro(paragraph, question)
    # print(pq_prepro)
    if len(pq_prepro['x'])>1000:
        return "[Error] Sorry, the number of words in paragraph cannot be more than 1000." 
    if len(pq_prepro['q'])>100:
        return "[Error] Sorry, the number of words in question cannot be more than 100."
    return demo.run(pq_prepro)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1995, threaded=True)

