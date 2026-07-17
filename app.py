from flask import Flask, render_template, request, jsonify, session
import os
import json
import re

app = Flask(__name__)
app.secret_key="mahitha_secret"
@app.route("/")
def home():
    return pyq()
@app.route('/pyq')
def pyq():
    questions_list = []
    
    # Force deep path directory lookup matching absolute path variables
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json'),
        # Alternate root search layout configurations
        os.path.abspath('dsa/questions/hr_questions.json'),
        os.path.abspath('questions/hr_questions.json')
    ]
    
    chosen_path = None
    for p in possible_paths:
        if os.path.exists(p):
            chosen_path = p
            break
            
    if chosen_path:
        try:
            with open(chosen_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                if isinstance(json_data, dict) and 'data' in json_data:
                    questions_list = json_data['data']
                elif isinstance(json_data, list):
                    questions_list = json_data
        except Exception as e:
            print(f"❌ JSON Decode Error: {e}")
    else:
        print("❌ FILE NOT FOUND. Please verify your file sits inside 'dsa/questions/hr_questions.json'")

    if 'solved_questions' not in session:
        session['solved_questions'] = []

    # Bind active state sync
    for q in questions_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session['solved_questions']]

    topics = {}
    for q in questions_list:
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)
        
        q_companies = q.get('companies', [])
        if isinstance(q_companies, list):
            for comp in q_companies:
                if len(topics[t_name]["top_companies"]) < 3:
                    topics[t_name]["top_companies"].add(str(comp).strip())

    for t in topics:
        topics[t]["top_companies"] = list(topics[t]["top_companies"])

    patterns = {}
    for q in questions_list:
        q_patterns = q.get('patterns', [])
        if isinstance(q_patterns, list) and q_patterns:
            for p_name in q_patterns:
                p_name = str(p_name).strip()
                if p_name not in patterns:
                    patterns[p_name] = {"questions": []}
                patterns[p_name]["questions"].append(q)
        else:
            p_name = "General Patterns"
            if p_name not in patterns:
                patterns[p_name] = {"questions": []}
            patterns[p_name]["questions"].append(q)

    # Calculate standard metric parameters dynamically
    total_q_count = len(questions_list) if questions_list else 117

    return render_template('PYQ.html', 
                           topics=topics, 
                           patterns=patterns, 
                           streak_count=session.get('streak_count', 0),
                           total_q_count=total_q_count)
@app.route('/api/update-pyq-status', methods=['POST'])

def update_pyq_status():
    data = request.get_json()
    q_id = str(data.get('id'))
    is_solved = data.get('solved')
    
    if 'solved_questions' not in session:
        session['solved_questions'] = []
        
    solved_list = list(session['solved_questions'])
    
    if is_solved and q_id not in solved_list:
        solved_list.append(q_id)
    elif not is_solved and q_id in solved_list:
        solved_list.remove(q_id)
        
    session['solved_questions'] = solved_list
    session.modified = True # Keep session sync alive in Flask
    
    return jsonify({"status": "success"})
@app.route('/pyq/must-solve')
def pyq_must_solve():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json')
    ]
    
    questions_list = []
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                questions_list = json_data.get('data', []) if isinstance(json_data, dict) else json_data
            break

    # Filter: Only keep true mustSolve items
    must_solve_list = [q for q in questions_list if q.get('mustSolve') is True or str(q.get('type')).lower() == 'must-do']

    topics = {}
    for q in must_solve_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session.get('solved_questions', [])]
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)
        for t in topics:
             topics[t]["top_companies"] = list(topics[t]["top_companies"])

    # Renders your dedicated must.html
    return render_template('must.html', topics=topics, streak_count=session.get('streak_count', 0))


@app.route('/pyq/most-repeated')
def pyq_most_repeated():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, 'dsa', 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'questions', 'hr_questions.json'),
        os.path.join(base_dir, 'hr_questions.json')
    ]
    
    questions_list = []
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                questions_list = json_data.get('data', []) if isinstance(json_data, dict) else json_data
            break

    # Filter: Keep high frequency repeated items, sorted high to low
    repeated_list = [q for q in questions_list if int(q.get('repeated', 1)) > 2]
    repeated_list.sort(key=lambda x: int(x.get('repeated', 1)), reverse=True)

    topics = {}
    for q in repeated_list:
        q['solved'] = str(q.get('id')) in [str(x) for x in session.get('solved_questions', [])]
        t_name = str(q.get('topic', 'Arrays')).strip()
        if t_name not in topics:
            topics[t_name] = {"questions": [], "top_companies": set()}
        topics[t_name]["questions"].append(q)


    for t in topics:
        topics[t]["top_companies"] = list(topics[t]["top_companies"])

    # Renders your dedicated repeated.html
    return render_template('repeated.html', topics=topics, streak_count=session.get('streak_count', 0))
if __name__ == "__main__":
    app.run(debug=True)