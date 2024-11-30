from flask import Flask, request, render_template #download flask
from query import Query
app = Flask(__name__)

 #run the code and click the link when it says ' Running on <whatever the link is>'
@app.route('/')
def my_form():
    return render_template('search-UI.html')
@app.route('/', methods=['POST'])
def run_query():
    text = request.form['query']
    q = Query()
    links = q.get_user_input(text)
    #links = ["https://memory.toys/classic/easy/", "https://alwaysjudgeabookbyitscover.com/", "https://memory.toys/classic/easy/", "https://alwaysjudgeabookbyitscover.com/", "https://memory.toys/classic/easy/", "https://alwaysjudgeabookbyitscover.com/", "https://memory.toys/classic/easy/", "https://alwaysjudgeabookbyitscover.com/", "https://memory.toys/classic/easy/", "https://alwaysjudgeabookbyitscover.com/"]
    #work on return render_template('results.html', links) so we can refresh and render a new html page with these links
    #this just returns a page with links
    return render_template('results.html', links=links)

if __name__ == '__main__':
    app.run(debug=True)
