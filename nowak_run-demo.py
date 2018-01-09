from flask import Flask, render_template, redirect, request, jsonify
from squad.demo_prepro import prepro
from basic.demo_cli import Demo
import json
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Instantiate demo from basic.demo_cli
demo = Demo()


@app.route('/allen', methods=['GET'])
def allen():
    # What is the user ID of the person TO WHOM we are asking question?
    # This will effect document retrieval.
    id = request.args.get('id', default = 7606, type = int)
    # We will need to use a document retreiver to get this document.
    paragraph = "A chatbot (also known as a talkbot, chatterbot, Bot, IM bot, interactive agent, or Artificial Conversational Entity) is a computer program which conducts a conversation via auditory or textual methods.[1] Such programs are often designed to convincingly simulate how a human would behave as a conversational partner, thereby passing the Turing test. Chatbots are typically used in dialog systems for various practical purposes including customer service or information acquisition. Some chatterbots use sophisticated natural language processing systems, but many simpler systems scan for keywords within the input, then pull a reply with the most matching keywords, or the most similar wording pattern, from a database."
    # User submits questoin in API GET call.
    query = request.args.get('query', default = "What is a chatbot?", type = str)  
    answer = getAnswer(paragraph, query)
    # Create empty dictionary to place answer into.
    d = {}
    d['span'] = answer # Call the answer span:
    return jsonify(d)

def getAnswer(paragraph, question):
    pq_prepro = prepro(paragraph, question)
    print(pq_prepro)
    if len(pq_prepro['x'])>1000:
        return "[Error] Sorry, the number of words in paragraph cannot be more than 1000." 
    if len(pq_prepro['q'])>100:
        return "[Error] Sorry, the number of words in question cannot be more than 100."
    return demo.run(pq_prepro)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=1995, threaded=True)
