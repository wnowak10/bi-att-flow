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
    dox = "https://molly.com/q?q=how%20should%20we%20decide%20which%20features%20to%20build?&id="+str(respondent_id)
    with urllib.request.urlopen(dox) as url:
            molly_data = json.loads(url.read().decode())

    # # Fill texts, create id dictionary to map each text to its Molly ID
    # molly_texts = []
    # molly_ids = []
    # id_dict= {}
    # for i, post in enumerate(molly_data['blog']):
    #     molly_ids.append(i)
    #     id_dict[i] = str(molly_data['blog'][i]['id'])
    #     molly_texts.append(post.get('content'))
    query = request.args.get('query', default = "What is SocialCam?", type = str) 

    molly_texts = []
    molly_ids = []
    ids_list = []
    for data_source in molly_data:
        if data_source == 'blog':
            for i, post in enumerate(molly_data[data_source], start = 0):
                molly_data[data_source][i]['span'] = getAnswer(post.get('content'), query)
                # molly_data[data_source][i]['span'] = getAnswer(post.get('content'), query)
                # molly_texts.append(post.get('content'))
                # molly_ids.append(post['id'])
                # ids_list.append(str(molly_data[data_source][i]['id']))
        elif data_source == 'answer':
            for j, response in enumerate(molly_data[data_source]):
                molly_data[data_source][j]['span'] = getAnswer(response.get('comments'), query)

    #             molly_texts.append(response.get('comments'))
    #             ids_list.append(str(molly_data[data_source][j]['id']))
        elif data_source == 'twitter':
            for k, tweet in enumerate(molly_data[data_source]):
                molly_data[data_source][k]['span'] = getAnswer(tweet.get('text'), query)

    #             molly_texts.append(tweet.get('text'))
    #             ids_list.append(str(molly_data[data_source][k]['id']))
    # # User submits questoin in API GET call.
    # query = request.args.get('query', default = "What is SocialCam?", type = str) 


    # answers = {}
    # for i, paragraph in enumerate(molly_texts):
    #     answers[ids_list[i]] = getAnswer(paragraph, query)
    # Create empty dictionary to place answer into.
    # d = {}
    # d['span'] = answer # Call the answer span:
    # return jsonify(answers)
    molly_data['Q'] = query
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
