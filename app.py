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
        CREATE TABLE IF NOT EXISTS custom_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            workout TEXT NOT NULL,
            muscle TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

MACHINES = {
    "bench_press": {"name": "לחיצת חזה מוט (שטוח)", "category": "חזה", "type": "free", "workout": "push", "muscle": "חזה גדול, יד אחורית", "guide": "שכוב על הספסל ודחף את המוט למעלה."},
    "incline_bench": {"name": "לחיצת חזה עליון", "category": "חזה", "type": "free", "workout": "push", "muscle": "חזה עליון", "guide": "ספסל בשיפוע 30-45 מעלות."},
    "overhead_press": {"name": "לחיצת כתפיים במוט", "category": "כתפיים", "type": "free", "workout": "push", "muscle": "כתף קדמית", "guide": "דחף מוט מעל הראש בעמידה."},
    "pullups": {"name": "מתח (Pull-ups)", "category": "גב", "type": "free", "workout": "pull", "muscle": "רחב גבי ויד קדמית", "guide": "משוך חזה אל המוט."},
    "lat_pulldown": {"name": "פולי עליון רחב", "category": "גב", "type": "machine", "workout": "pull", "muscle": "רחב גבי", "guide": "משוך מוט לחזה."},
    "barbell_row": {"name": "חתירה במוט", "category": "גב", "type": "free", "workout": "pull", "muscle": "גב אמצעי", "guide": "התכופף ומשוך מוט לבטן."},
    "squat": {"name": "סקוואט חופשי", "category": "רגליים", "type": "free", "workout": "legs", "muscle": "ארבע-ראשי וישבן", "guide": "רד לעומק בשליטה."},
    "leg_press": {"name": "לחיצת רגליים", "category": "רגליים", "type": "machine", "workout": "legs", "muscle": "ארבע-ראשי", "guide": "דחף משקל בפלטפורמה."}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GymLog Pro Ultimate</title>
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
            --danger: #ef4444;
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
            --danger: #dc2626;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }
        body { background-color: var(--bg-color); color: var(--text-color); padding: 12px; transition: background 0.3s; padding-bottom: 60px; }
        
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; background: var(--card-bg); padding: 12px 16px; border-radius: 12px; border: 1px solid var(--border); }
        h1 { color: var(--accent); font-size: 20px; }

        .nav-tabs { display: flex; gap: 6px; margin-bottom: 12px; overflow-x: auto; padding-bottom: 4px; }
        .tab-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 8px 12px; border-radius: 10px; font-size: 13px; cursor: pointer; font-weight: bold; white-space: nowrap; flex: 1; text-align: center; }
        .tab-btn.active { background: var(--accent); color: #fff; border-color: var(--accent); }

        .section-view { display: none; }
        .section-view.active { display: block; }

        .timer-bar { background: var(--card-bg); border: 1px solid var(--border); padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
        
        .machine-card { background-color: var(--card-bg); border-radius: 14px; padding: 15px; margin-bottom: 12px; border: 1px solid var(--border); position: relative; }
        .machine-card.completed { border-color: var(--accent); opacity: 0.75; }
        
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
        .machine-title { font-size: 17px; font-weight: bold; color: var(--accent); }
        
        .done-checkbox { display: flex; align-items: center; gap: 5px; font-size: 12px; font-weight: bold; cursor: pointer; background: var(--input-bg); padding: 5px 8px; border-radius: 8px; border: 1px solid var(--border); }
        .done-checkbox input { width: 16px; height: 16px; accent-color: var(--accent); cursor: pointer; }

        .badge-group { display: flex; gap: 5px; margin-bottom: 8px; }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 7px; border-radius: 6px; font-size: 11px; border: 1px solid var(--border); }
        
        .section-title { font-size: 11px; color: var(--subtext); margin-top: 8px; }
        .muscle-info { font-size: 13px; color: var(--text-color); margin-bottom: 6px; }
        
        .suggestion-box { background: rgba(16, 185, 129, 0.1); border: 1px dashed var(--accent); padding: 8px; border-radius: 8px; font-size: 12px; color: var(--accent); margin-bottom: 8px; font-weight: bold; display: none; }
        .rm-box { font-size: 11px; color: var(--subtext); margin-bottom: 6px; }

        .form-group { display: flex; gap: 6px; margin-top: 8px; }
        input[type="number"], input[type="text"], select { flex: 1; padding: 9px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 13px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #fff; border: none; padding: 9px 14px; font-weight: bold; border-radius: 8px; cursor: pointer; font-size: 13px; }
        
        .history-box { margin-top: 10px; background: var(--input-bg); padding: 8px; border-radius: 8px; font-size: 11px; max-height: 90px; overflow-y: auto; color: var(--subtext); border: 1px solid var(--border); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 3px 0; }

        .program-selector { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 12px; }
        
        /* Builder Form */
        .builder-form { background: var(--card-bg); padding: 15px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 15px; }
        .builder-form input, .builder-form select { width: 100%; margin-bottom: 8px; text-align: right; }
    </style>
</head>
<body>
    <header>
        <h1>🏋️‍♂️ GymLog Pro</h1>
        <button class="tab-btn" onclick="toggleTheme()" style="padding: 5px 10px; flex: none;">🌓 תצוגה</button>
    </header>

    <!-- טיימר מנוחה מהיר -->
    <div class="timer-bar">
        <span>⏱️ מנוחה: <strong id="timerClock">00:00</strong></span>
        <div style="display:flex; gap:5px;">
            <button class="filter-btn" onclick="startTimer(90)" style="background:var(--input-bg); border:1px solid var(--border); color:var(--text-color); padding:4px 8px; border-radius:6px; cursor:pointer;">90 שניות</button>
            <button class="filter-btn" onclick="startTimer(120)" style="background:var(--input-bg); border:1px solid var(--border); color:var(--text-color); padding:4px 8px; border-radius:6px; cursor:pointer;">2 דקות</button>
        </div>
    </div>

    <!-- ניווט ראשי -->
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="switchTab('workoutTab', this)">📋 תוכנית אימון</button>
        <button class="tab-btn" onclick="switchTab('builderTab', this)">🛠️ בנה תוכנית</button>
        <button class="tab-btn" onclick="switchTab('allExercisesTab', this)">💪 כל התרגילים</button>
    </div>

    <!-- 1. טאב תוכנית אימון מובנית -->
    <div id="workoutTab" class="section-view active">
        <div class="program-selector">
            <button class="tab-btn active" onclick="selectProgram('push', this)">🔥 דחיפה</button>
            <button class="tab-btn" onclick="selectProgram('pull', this)">⚡ משיכה</button>
            <button class="tab-btn" onclick="selectProgram('legs', this)">🦵 רגליים</button>
        </div>

        <div id="programList">
            {% for id, m in machines.items() %}
            <div class="machine-card program-card" data-workout="{{ m.workout }}" id="card-{{ id }}">
                <div class="card-header">
                    <div class="machine-title">{{ m.name }}</div>
                    <label class="done-checkbox">
                        <input type="checkbox" onchange="toggleDone('{{ id }}', this)"> בוצע V
                    </label>
                </div>

                <div class="badge-group">
                    <span class="badge">{{ m.category }}</span>
                    <span class="badge">{% if m.type == 'free' %}משקל חופשי{% else %}מכונה{% endif %}</span>
                </div>
                
                <div class="muscle-info">🎯 שריר: {{ m.muscle }}</div>
                
                <!-- המלצה חכמה לעליית משקל -->
                <div class="suggestion-box" id="suggestion-{{ id }}">
                    💡 המלצה: עברת 8 חזרות באימון קודם! נסה לעלות משקל היום 🚀
                </div>

                <div class="rm-box" id="rm-{{ id }}">מקסימום משוער (1RM): חישוב יופיע לאחר שמירה</div>
                
                <form onsubmit="saveWeight(event, '{{ id }}')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-{{ id }}" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-{{ id }}" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור</button>
                    </div>
                </form>

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

            <!-- תרגילים מותאמים אישית שנוספו -->
            {% for c in custom_exercises %}
            <div class="machine-card program-card" data-workout="{{ c[3] }}" id="card-custom-{{ c[0] }}">
                <div class="card-header">
                    <div class="machine-title">{{ c[1] }} (מותאם אישית)</div>
                    <label class="done-checkbox">
                        <input type="checkbox" onchange="toggleDone('custom-{{ c[0] }}', this)"> בוצע V
                    </label>
                </div>

                <div class="badge-group">
                    <span class="badge">{{ c[2] }}</span>
                    <span class="badge">מותאם אישית</span>
                </div>
                
                <div class="muscle-info">🎯 שריר: {{ c[4] }}</div>

                <form onsubmit="saveWeight(event, 'custom-{{ c[0] }}')">
                    <div class="form-group">
                        <input type="number" step="0.5" id="weight-custom-{{ c[0] }}" placeholder="משקל (ק״ג)" required>
                        <input type="number" id="reps-custom-{{ c[0] }}" placeholder="חזרות" required>
                        <button type="submit" class="save-btn">שמור</button>
                    </div>
                </form>

                <div class="history-box" id="history-custom-{{ c[0] }}">
                    {% if history['custom-' ~ c[0]] %}
                        {% for h in history['custom-' ~ c[0]] %}
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

    <!-- 2. טאב בורא תוכניות אימון אישיות -->
    <div id="builderTab" class="section-view">
        <div class="builder-form">
            <h3 style="margin-bottom:10px; color:var(--accent);">הוסף תרגיל חדש לתוכנית שלך</h3>
            <form action="/api/add_custom_exercise" method="POST">
                <input type="text" name="name" placeholder="שם התרגיל (למשל: דאמבל פליי)" required>
                <select name="category" required>
                    <option value="חזה">חזה</option>
                    <option value="גב">גב</option>
                    <option value="כתפיים">כתפיים</option>
                    <option value="רגליים">רגליים</option>
                    <option value="ידיים">ידיים</option>
                    <option value="בטן">בטן</option>
                </select>
                <select name="workout" required>
                    <option value="push">דחיפה (Push)</option>
                    <option value="pull">משיכה (Pull)</option>
                    <option value="legs">רגליים (Legs)</option>
                </select>
                <input type="text" name="muscle" placeholder="שרירים פועלים (למשל: חזה עליון)" required>
                <button type="submit" class="save-btn" style="width:100%;">הוסף תרגיל למערכת ➕</button>
            </form>
        </div>
    </div>

    <!-- 3. טאב כל התרגילים -->
    <div id="allExercisesTab" class="section-view">
        <div id="allList">
            {% for id, m in machines.items() %}
            <div class="machine-card">
                <div class="machine-title">{{ m.name }}</div>
                <div class="badge-group"><span class="badge">{{ m.category }}</span></div>
                <div class="muscle-info">🎯 {{ m.muscle }}</div>
                <div style="font-size:12px; color:var(--subtext); margin-top:5px;">💡 {{ m.guide }}</div>
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

        function selectProgram(prog, btn) {
            document.querySelectorAll('.program-selector .tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.program-card').forEach(card => {
                if (card.getAttribute('data-workout') === prog) {
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

                // חישוב 1RM משוער: משקל * (1 + חזרות / 30)
                const oneRepMax = Math.round(weight * (1 + reps / 30));
                document.getElementById(`rm-${machineId}`).innerText = `🔥 שיא חזרה אחת משוער (1RM): ${oneRepMax} ק״ג`;

                // בדיקת המלצת עליית משקל
                if (reps >= 8) {
                    document.getElementById(`suggestion-${machineId}`).style.display = 'block';
                }

                document.getElementById(`weight-${machineId}`).value = '';
                document.getElementById(`reps-${machineId}`).value = '';
                alert('נשמר בהצלחה! 💪');
            }
        }

        let countdown;
        function startTimer(seconds) {
            clearInterval(countdown);
            let timeLeft = seconds;
            const display = document.getElementById('timerClock');
            
            countdown = setInterval(() => {
                let m = Math.floor(timeLeft / 60);
                let s = timeLeft % 60;
                display.innerText = `${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
                if (timeLeft <= 0) {
                    clearInterval(countdown);
                    alert('נגמרה המנוחה! קח סט חדש 🏋️‍♂️');
                }
                timeLeft--;
            }, 1000);
        }

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
    
    cursor.execute("SELECT id, name, category, workout, muscle FROM custom_exercises")
    custom_exercises = cursor.fetchall()
    conn.close()

    history = {}
    for r in rows:
        m_id, w, reps, d = r[0], r[1], r[2], r[3]
        if m_id not in history:
            history[m_id] = []
        history[m_id].append((w, reps, d))

    return render_template_string(HTML_TEMPLATE, machines=MACHINES, custom_exercises=custom_exercises, history=history)

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

@app.route('/api/add_custom_exercise', methods=['POST'])
def add_custom_exercise():
    name = request.form.get('name')
    category = request.form.get('category')
    workout = request.form.get('workout')
    muscle = request.form.get('muscle')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO custom_exercises (name, category, workout, muscle) VALUES (?, ?, ?, ?)", (name, category, workout, muscle))
    conn.commit()
    conn.close()

    return '''
        <script>
            alert('התרגיל נוסף בהצלחה לתוכנית שלך! 🎉');
            window.location.href = '/';
        </script>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
