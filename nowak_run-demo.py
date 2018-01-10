from flask import Flask, render_template, redirect, request, jsonify
from squad.demo_prepro import prepro
from basic.demo_cli import Demo
import json
from flask_cors import CORS
import urllib

app = Flask(__name__)
CORS(app)

# Instantiate demo from basic.demo_cli
demo = Demo()


@app.route('/allen', methods=['GET'])
def allen():
    # What is the user ID of the person TO WHOM we are asking question?
    # This will effect document retrieval.
    respondent_id = request.args.get('id', default = 7606, type = int)

    # We will need to use a document retreiver to get this document.
    # At the moment, just reading from these blog posts.
    dox = "https://molly.com/q?q=how%20should%20we%20decide%20which%20features%20to%20build?&id=7606"
    with urllib.request.urlopen(dox) as url:
            molly_data = json.loads(url.read().decode())

    # Fill texts, create id dictionary to map each text to its Molly ID
    molly_texts = []
    molly_ids = []
    id_dict= {}
    for i, post in enumerate(molly_data['blog']):
        molly_ids.append(i)
        id_dict[i] = str(molly_data['blog'][i]['id'])
        molly_texts.append(post.get('content'))


    # User submits questoin in API GET call.
    query = request.args.get('query', default = "What is the best press advice you ever received?", type = str) 
    answers = {}
    for i, paragraph in enumerate(molly_texts):
        answers[id_dict[i]] = getAnswer(paragraph, query)
    # Create empty dictionary to place answer into.
    # d = {}
    # d['span'] = answer # Call the answer span:
    return jsonify(answers)

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
