from flask import Flask, render_template_string, request, jsonify
import sqlite3

app = Flask(__name__)
DB_NAME = "gym.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id TEXT NOT NULL,
            weight REAL NOT NULL,
            reps INTEGER NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workout_type TEXT NOT NULL,
            exercise_id TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# מאגר מקיף של תרגילים לבחירה
ALL_EXERCISES = {
    "bench_press": {"name": "לחיצת חזה מוט (שטוח)", "category": "חזה", "workout": "push"},
    "incline_bench": {"name": "לחיצת חזה עליון", "category": "חזה", "workout": "push"},
    "dumbbell_press": {"name": "לחיצת חזה דאמבלים", "category": "חזה", "workout": "push"},
    "pec_fly": {"name": "פרפר / קירוב חזה", "category": "חזה", "workout": "push"},
    "overhead_press": {"name": "לחיצת כתפיים במוט", "category": "כתפיים", "workout": "push"},
    "lateral_raise": {"name": "הרחקת כתפיים לצדדים", "category": "כתפיים", "workout": "push"},
    "triceps_pushdown": {"name": "פשיטת מרפקים בפולי (יד אחורית)", "category": "ידיים", "workout": "push"},
    
    "pullups": {"name": "מתח (Pull-ups)", "category": "גב", "workout": "pull"},
    "lat_pulldown": {"name": "פולי עליון רחב", "category": "גב", "workout": "pull"},
    "barbell_row": {"name": "חתירה במוט", "category": "גב", "workout": "pull"},
    "seated_row": {"name": "חתירה בישיבה פולי תחתון", "category": "גב", "workout": "pull"},
    "biceps_curl": {"name": "כפיפת מרפקים (יד קדמית)", "category": "ידיים", "workout": "pull"},
    
    "squat": {"name": "סקוואט חופשי", "category": "רגליים", "workout": "legs"},
    "leg_press": {"name": "לחיצת רגליים (Leg Press)", "category": "רגליים", "workout": "legs"},
    "leg_extension": {"name": "פשיטת ברכיים (ירך קדמית)", "category": "רגליים", "workout": "legs"},
    "leg_curl": {"name": "כפיפת ברכיים (ירך אחורית)", "category": "רגליים", "workout": "legs"},
    "calf_raise": {"name": "הרים שוקיים / תאומים", "category": "רגליים", "workout": "legs"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GymLog Pro Ultimate</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #151b2b;
            --text-color: #f3f4f6;
            --subtext: #9ca3af;
            --accent: #10b981;
            --accent-hover: #059669;
            --border: #1f293d;
            --input-bg: #1e2538;
        }
        .light-mode {
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-color: #1f2937;
            --subtext: #4b5563;
            --accent: #2563eb;
            --accent-hover: #1d4ed8;
            --border: #e5e7eb;
            --input-bg: #f9fafb;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }
        body { background-color: var(--bg-color); color: var(--text-color); padding: 12px; transition: background 0.3s; padding-bottom: 60px; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; background: var(--card-bg); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }
        h1 { color: var(--accent); font-size: 20px; }

        .nav-tabs { display: flex; gap: 6px; margin-bottom: 12px; overflow-x: auto; }
        .tab-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 8px 12px; border-radius: 10px; font-size: 13px; cursor: pointer; font-weight: bold; flex: 1; text-align: center; white-space: nowrap; }
        .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .section-view { display: none; }
        .section-view.active { display: block; }

        .machine-card { background-color: var(--card-bg); border-radius: 14px; padding: 15px; margin-bottom: 12px; border: 1px solid var(--border); }
        .machine-card.completed { border-color: var(--accent); opacity: 0.75; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .machine-title { font-size: 17px; font-weight: bold; color: var(--accent); }
        
        .done-checkbox { display: flex; align-items: center; gap: 5px; font-size: 12px; font-weight: bold; cursor: pointer; background: var(--input-bg); padding: 5px 8px; border-radius: 8px; border: 1px solid var(--border); }
        .done-checkbox input { width: 16px; height: 16px; accent-color: var(--accent); cursor: pointer; }

        .badge-group { display: flex; gap: 5px; margin-bottom: 8px; }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 7px; border-radius: 6px; font-size: 11px; border: 1px solid var(--border); }
        
        .suggestion-box { background: rgba(16, 185, 129, 0.15); border: 1px dashed var(--accent); padding: 8px; border-radius: 8px; font-size: 12px; color: var(--accent); margin-bottom: 8px; font-weight: bold; display: none; }
        
        .form-group { display: flex; gap: 6px; margin-top: 8px; }
        input[type="number"], select { flex: 1; padding: 9px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 13px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #fff; border: none; padding: 9px 14px; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 13px; }
        
        .history-box { margin-top: 10px; background: var(--input-bg); padding: 8px; border-radius: 8px; font-size: 11px; max-height: 80px; overflow-y: auto; color: var(--subtext); border: 1px solid var(--border); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 3px 0; }

        .program-selector { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }
        
        .builder-box { background: var(--card-bg); padding: 15px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 15px; }
        .chart-container { margin-top: 10px; background: var(--input-bg); padding: 8px; border-radius: 8px; border: 1px solid var(--border); }
    </style>
</head>
<body>
    <header>
        <h1>🏋️‍♂️ GymLog Pro</h1>
        <button class="tab-btn" onclick="toggleTheme()" style="padding: 5px 10px; flex: none;">🌓 תצוגה</button>
    </header>

    <!-- ניווט ראשי -->
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('workoutTab', this)">📋 תוכנית אימון</button>
        <button class="tab-btn" onclick="switchTab('builderTab', this)">🛠️ בחר תרגילים לתוכנית</button>
        <button class="tab-btn" onclick="switchTab('allExercisesTab', this)">💪 קטגוריות ותרגילים</button>
    </div>

    <!-- 1. טאב תוכנית אימון -->
    <div id="workoutTab" class="section-view active">
        <div class="program-selector">
            <button class="tab-btn active" onclick="selectProgram('push', this)">🔥 דחיפה</button>
            <button class="tab-btn" onclick="selectProgram('pull', this)">⚡ משיכה</button>
            <button class="tab-btn" onclick="selectProgram('legs', this)">🦵 רגליים</button>
        </div>

        <div id="programList">
            {% for id, ex in all_exercises.items() %}
            <div class="machine-card program-card" data-workout="{{ ex.workout }}" id="card-{{ id }}" style="display: none;">
                <div class="card-header">
                    <div class="machine-title">{{ ex.name }}</div>
                    <label class="done-checkbox">
                        <input type="checkbox" onchange="toggleDone('{{ id }}', this)"> בוצע V
                    </label>
                </div>

                <div class="badge-group">
                    <span class="badge">{{ ex.category }}</span>
                </div>
                
                <!-- המלצה לעליית משקל כשמגיעים ל-10 חזרות -->
                <div class="suggestion-box" id="suggestion-{{ id }}">
                    🔥 הגעת ל-10 חזרות או יותר! אל תפחד, הגיע הזמן לעלות משקל! 🚀
                </div>
                
                <form onsubmit="saveWeight(event, '{{ id }}')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-{{ id }}" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-{{ id }}" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור</button>
                    </div>
                </form>

                <!-- גרף התקדמות -->
                <div class="chart-container">
                    <canvas id="chart-{{ id }}"></canvas>
                </div>

                <div class="history-box" id="history-{{ id }}">
                    {% if history[id] %}
                        {% for h in history[id] %}
                        <div class="history-item">
                            <span><strong>{{ h[0] }} ק״ג</strong> x {{ h[1] }} חזרות</span>
                            <span>{{ h[2][:16] }}</span>
                        </div>
                        {% endfor %}
                    {% else %}
                        <span>טרם נרשמו אימונים</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- 2. טאב בחירת תרגילים מתוך רשימה -->
    <div id="builderTab" class="section-view">
        <div class="builder-box">
            <h3 style="margin-bottom:10px; color:var(--accent);">בחר אילו תרגילים להוסיף לתוכניות שלך</h3>
            <form action="/api/save_custom_workout" method="POST">
                <select name="workout_type" style="margin-bottom:10px;" required>
                    <option value="push">יום דחיפה (Push)</option>
                    <option value="pull">יום משיכה (Pull)</option>
                    <option value="legs">יום רגליים (Legs)</option>
                </select>
                <select name="exercise_id" style="margin-bottom:10px;" required>
                    {% for id, ex in all_exercises.items() %}
                    <option value="{{ id }}">{{ ex.name }} ({{ ex.category }})</option>
                    {% endfor %}
                </select>
                <button type="submit" class="save-btn" style="width:100%;">הוסף תרגיל לתוכנית ➕</button>
            </form>
        </div>
    </div>

    <!-- 3. טאב קטגוריות ותרגילים -->
    <div id="allExercisesTab" class="section-view">
        <div style="display:flex; flex-direction:column; gap:10px;">
            {% for id, ex in all_exercises.items() %}
            <div class="machine-card">
                <div class="machine-title">{{ ex.name }}</div>
                <div class="badge-group"><span class="badge">קטגוריה: {{ ex.category }}</span></div>
            </div>
            {% endfor %}
        </div>
    </div>

    <script>
        function toggleTheme() { document.body.classList.toggle('light-mode'); }

        function switchTab(tabId, btn) {
            document.querySelectorAll('.section-view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-tabs .tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            btn.classList.add('active');
        }

        const activeUserExercises = {{ active_exercises | tojson }};

        function selectProgram(prog, btn) {
            document.querySelectorAll('.program-selector .tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.program-card').forEach(card => {
                const cardId = card.id.replace('card-', '');
                const workout = card.getAttribute('data-workout');
                // מציג רק תרגילים ששייכים ליום ושנבחרו על ידי המשתמש
                if (workout === prog && activeUserExercises[prog] && activeUserExercises[prog].includes(cardId)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function toggleDone(id, checkbox) {
            const card = document.getElementById(`card-${id}`);
            if (checkbox.checked) { card.classList.add('completed'); } 
            else { card.classList.remove('completed'); }
        }

        async function saveWeight(e, machineId) {
            e.preventDefault();
            const weight = parseFloat(document.getElementById(`weight-${machineId}`).value);
            const reps = parseInt(document.getElementById(`reps-${machineId}`).value);

            const res = await fetch('/api/add_weight', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({machine_id: machineId, weight: weight, reps: reps})
            });

            if(res.ok) {
                const data = await res.json();
                const historyBox = document.getElementById(`history-${machineId}`);
                if(historyBox.innerHTML.includes('טרם נרשמו')) { historyBox.innerHTML = ''; }

                const newItem = document.createElement('div');
                newItem.className = 'history-item';
                newItem.innerHTML = `<span><strong>${weight} ק״ג</strong> x ${reps} חזרות</span><span>${data.date.substring(0,16)}</span>`;
                historyBox.prepend(newItem);

                // בדיקת המלצת עליית משקל מעל 10 חזרות
                if (reps >= 10) {
                    document.getElementById(`suggestion-${machineId}`).style.display = 'block';
                }

                document.getElementById(`weight-${machineId}`).value = '';
                document.getElementById(`reps-${machineId}`).value = '';
                alert('נשמר בהצלחה! 💪');
                location.reload();
            }
        }

        // יצירת גרפים דינמיים לכל תרגיל
        const historyData = {{ history_json | safe }};
        Object.keys(historyData).forEach(exId => {
            const canvasEl = document.getElementById(`chart-${exId}`);
            if (canvasEl && historyData[exId].length > 0) {
                const sorted = historyData[exId].slice().reverse();
                const weights = sorted.map(h => h[0]);
                const dates = sorted.map(h => h[2].substring(5, 16));

                new Chart(canvasEl, {
                    type: 'line',
                    data: {
                        labels: dates,
                        datasets: [{
                            label: 'משקל (ק״ג)',
                            data: weights,
                            borderColor: '#10b981',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 2,
                            tension: 0.2,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: { x: { display: false }, y: { ticks: { font: { size: 10 }, color: '#9ca3af' } } }
                    }
                });
            }
        });

        // הפעלה ראשונית של תוכנית דחיפה
        selectProgram('push', document.querySelector('.program-selector .tab-btn'));
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT machine_id, weight, reps, date FROM weights ORDER BY id DESC")
    rows = cursor.fetchall()
    
    cursor.execute("SELECT workout_type, exercise_id FROM custom_workouts")
    custom_rows = cursor.fetchall()
    conn.close()

    history = {}
    for r in rows:
        m_id, w, reps, d = r[0], r[1], r[2], r[3]
        if m_id not in history:
            history[m_id] = []
        history[m_id].append((w, reps, d))

    active_exercises = {"push": [], "pull": [], "legs": []}
    for cr in custom_rows:
        w_type, e_id = cr[0], cr[1]
        if w_type in active_exercises and e_id in ALL_EXERCISES and e_id not in active_exercises[w_type]:
            active_exercises[w_type].append(e_id)

    # ברירת מחדל אם אין תרגילים מוגדרים
    if not active_exercises["push"]:
        active_exercises["push"] = ["bench_press", "overhead_press"]
    if not active_exercises["pull"]:
        active_exercises["pull"] = ["pullups", "lat_pulldown"]
    if not active_exercises["legs"]:
        active_exercises["legs"] = ["squat", "leg_press"]

    return render_template_string(HTML_TEMPLATE, all_exercises=ALL_EXERCISES, active_exercises=active_exercises, history=history, history_json=str(history).replace("'", '"'))

@app.route('/api/add_weight', methods=['POST'])
def add_weight():
    data = request.json
    machine_id = data.get('machine_id')
    weight = data.get('weight')
    reps = data.get('reps')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO weights (machine_id, weight, reps) VALUES (?, ?, ?)", (machine_id, weight, reps))
    conn.commit()
    cursor.execute("SELECT datetime('now', '+3 hours')")
    date_str = cursor.fetchone()[0]
    conn.close()

    return jsonify({"success": True, "date": date_str})

@app.route('/api/save_custom_workout', methods=['POST'])
def save_custom_workout():
    workout_type = request.form.get('workout_type')
    exercise_id = request.form.get('exercise_id')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # מניעת כפילויות
    cursor.execute("SELECT id FROM custom_workouts WHERE workout_type = ? AND exercise_id = ?", (workout_type, exercise_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO custom_workouts (workout_type, exercise_id) VALUES (?, ?)", (workout_type, exercise_id))
        conn.commit()
    conn.close()

    return '''
        <script>
            alert('התרגיל נוסף בהצלחה לתוכנית האימון שלך! 🎉');
            window.location.href = '/';
        </script>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
