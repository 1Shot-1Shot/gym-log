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
    conn.commit()
    conn.close()

init_db()

MACHINES = {
    "chest_press": {"name": "לחיצת חזה שטוחה במכונה", "category": "חזה", "muscle": "חזה גדול, כתף קדמית, יד אחורית", "guide": "שב בצמוד למשענת, דחף לפנים עד יישור כמעט מלא.", "video_url": "https://www.youtube.com/embed/sqOw2Y6uDWQ"},
    "incline_chest": {"name": "לחיצת חזה בשיפוע עליון", "category": "חזה", "muscle": "חזה עליון, כתף קדמית", "guide": "כוון את המושב כך שהידיות מול החזה העליון.", "video_url": "https://www.youtube.com/embed/5CIDWJv6Xb8"},
    "pec_fly": {"name": "פרפר / קירוב חזה", "category": "חזה", "muscle": "חזה גדול", "guide": "שמור על מרפקים מעט כפופים וקרב את הזרועות.", "video_url": "https://www.youtube.com/embed/Z57CtZuYxug"},
    "cable_crossover": {"name": "קרוס אובר / פולי כפול", "category": "חזה", "muscle": "חזה עליון ואמצעי", "guide": "משוך את הכבלים בתנועה קשתית אל מרכז הגוף.", "video_url": "https://www.youtube.com/embed/taI4XduLlvQ"},
    
    "lat_pulldown": {"name": "פולי עליון רחב", "category": "גב", "muscle": "רחב גבי (Latissimus Dorsi), יד קדמית", "guide": "אחוז אחיזה רחבה ומשוך את המוט לחזה.", "video_url": "https://www.youtube.com/embed/CAwf7n6Luuc"},
    "seated_row": {"name": "חתירה בישיבה (פולי תחתון)", "category": "גב", "muscle": "גב אמצעי, רחב גבי", "guide": "משוך את הידיות לטבור תוך הידוק שכמות.", "video_url": "https://www.youtube.com/embed/GZbfZ033fBo"},
    "t_bar_row": {"name": "מכשיר T-Bar Row", "category": "גב", "muscle": "גב עליון ותחתון", "guide": "הישען קדימה ומשוך את המשקל אליך.", "video_url": "https://www.youtube.com/embed/j_D6FAuCvfU"},
    "back_extension": {"name": "כיסא רומי / פשיטת גו", "category": "גב", "muscle": "גב תחתון, ישבן", "guide": "הרם את פלג הגוף העליון בקו ישר.", "video_url": "https://www.youtube.com/embed/ph3pddkdko8"},

    "shoulder_press": {"name": "לחיצת כתפיים במכונה", "category": "כתפיים", "muscle": "כתף קדמית ואמצעית", "guide": "דחף את הידיות כלפי מעלה מבלי לנעול מרפקים.", "video_url": "https://www.youtube.com/embed/WvLMauqrnK8"},
    "reverse_fly": {"name": "פרפר הפוך לכתף אחורית", "category": "כתפיים", "muscle": "כתף אחורית, שכמות", "guide": "פתח את הזרועות אחורה כנגד ההתנגדות.", "video_url": "https://www.youtube.com/embed/0G2_95CkVg8"},
    "lateral_raise": {"name": "מכשיר הרחקת זרועות לצדדים", "category": "כתפיים", "muscle": "כתף אמצעית", "guide": "הרם את המרפקים לצדדים בגובה הכתפיים.", "video_url": "https://www.youtube.com/embed/PusVb_Ku_eY"},

    "leg_press": {"name": "לחיצת רגליים (45 מעלות)", "category": "רגליים", "muscle": "ארבע-ראשי, ישבן", "guide": "מקם רגליים ברוחב כתפיים ודחף את הפלטפורמה.", "video_url": "https://www.youtube.com/embed/IZxyjW7MPJQ"},
    "leg_extension": {"name": "פשטת ברכיים (ירך קדמית)", "category": "רגליים", "muscle": "ארבע-ראשי (Quadriceps)", "guide": "ישר את הברכיים כלפי מעלה ורד לאט.", "video_url": "https://www.youtube.com/embed/YyvSfVjQeL0"},
    "leg_curl": {"name": "כפיפת ברכיים (ירך אחורית)", "category": "רגליים", "muscle": "המסטרינג (Hamstrings)", "guide": "כופף את הרגליים לאחור כנגד הכרית.", "video_url": "https://www.youtube.com/embed/1T5Kjn7x91w"},
    "hack_squat": {"name": "האק סקוואט (Hack Squat)", "category": "רגליים", "muscle": "ארבע-ראשי, ישבן", "guide": "רד לעומק בשליטה מלאה ועלה חזרה.", "video_url": "https://www.youtube.com/embed/0tn5K9NlCfo"},
    "calf_raise": {"name": "מכשיר תאומים בעמידה", "category": "רגליים", "muscle": "שוקיים (Calves)", "guide": "עלה על קצות האצבעות והתרת עקב למטה.", "video_url": "https://www.youtube.com/embed/YMme0n7Bedw"},

    "biceps_curl": {"name": "כפיפת מרפקים (יד קדמית)", "category": "ידיים", "muscle": "יד קדמית (Biceps)", "guide": "הרם את הידיות לעבר הכתפיים בשליטה.", "video_url": "https://www.youtube.com/embed/ykJmrZ5v0Oo"},
    "triceps_extension": {"name": "פשיטת מרפקים (יד אחורית)", "category": "ידיים", "muscle": "יד אחורית (Triceps)", "guide": "דחף את הידיות כלפי מטה עד יישור הזרועות.", "video_url": "https://www.youtube.com/embed/nAh_Kxfeh5Q"},

    "ab_crunch": {"name": "מכשיר כפיפות בטן", "category": "בטן", "muscle": "שרירי הבטן הישירים", "guide": "כופף את הגו קדימה כנגד המשקל.", "video_url": "https://www.youtube.com/embed/2-w9bqa5t1s"}
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GymLog Pro</title>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #ffffff;
            --subtext: #aaaaaa;
            --accent: #00e676;
            --border: #2c2c2c;
            --input-bg: #2a2a2a;
        }
        .light-mode {
            --bg-color: #f4f4f9;
            --card-bg: #ffffff;
            --text-color: #222222;
            --subtext: #666666;
            --accent: #0070f3;
            --border: #dddddd;
            --input-bg: #eeeeee;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; }
        body { background-color: var(--bg-color); color: var(--text-color); padding: 15px; transition: background 0.3s, color 0.3s; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        h1 { color: var(--accent); font-size: 22px; }
        .theme-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        
        .controls { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
        input.search-box { width: 100%; padding: 12px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 10px; font-size: 15px; }
        .filters { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 5px; }
        .filter-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 6px 12px; border-radius: 20px; font-size: 13px; cursor: pointer; white-space: nowrap; }
        .filter-btn.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: bold; }

        .machine-card { background-color: var(--card-bg); border-radius: 12px; padding: 16px; margin-bottom: 15px; border: 1px solid var(--border); }
        .machine-title { font-size: 18px; font-weight: bold; color: var(--accent); }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 8px; border-radius: 6px; font-size: 12px; margin-top: 4px; }
        .section-title { font-size: 13px; color: var(--subtext); margin-top: 10px; }
        .muscle-info { font-size: 14px; color: var(--text-color); margin-bottom: 6px; }
        .guide-info { font-size: 13px; color: var(--subtext); line-height: 1.4; margin-bottom: 10px; }
        iframe { width: 100%; height: 180px; border-radius: 8px; border: none; margin-bottom: 12px; }
        
        .form-group { display: flex; gap: 8px; margin-top: 10px; }
        input[type="number"] { flex: 1; padding: 10px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 14px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #000; border: none; padding: 10px 15px; font-weight: bold; border-radius: 8px; cursor: pointer; }
        
        .history-box { margin-top: 12px; background: var(--input-bg); padding: 10px; border-radius: 8px; font-size: 12px; max-height: 100px; overflow-y: auto; color: var(--subtext); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 4px 0; }
    </style>
</head>
<body>
    <header>
        <h1>GymLog Pro 🏋️‍♂️</h1>
        <button class="theme-btn" onclick="toggleTheme()">🌓 מצב תצוגה</button>
    </header>

    <div class="controls">
        <input type="text" id="searchBox" class="search-box" placeholder="חפש מכונה או תרגיל..." oninput="filterMachines()">
        <div class="filters">
            <button class="filter-btn active" onclick="setCategory('הכל', this)">הכל</button>
            <button class="filter-btn" onclick="setCategory('חזה', this)">חזה</button>
            <button class="filter-btn" onclick="setCategory('גב', this)">גב</button>
            <button class="filter-btn" onclick="setCategory('כתפיים', this)">כתפיים</button>
            <button class="filter-btn" onclick="setCategory('רגליים', this)">רגליים</button>
            <button class="filter-btn" onclick="setCategory('ידיים', this)">ידיים</button>
            <button class="filter-btn" onclick="setCategory('בטן', this)">בטן</button>
        </div>
    </div>

    <div id="machinesList">
        {% for id, m in machines.items() %}
        <div class="machine-card" data-name="{{ m.name }}" data-category="{{ m.category }}">
            <div class="machine-title">{{ m.name }}</div>
            <span class="badge">{{ m.category }}</span>
            
            <div class="section-title">שרירים פועלים:</div>
            <div class="muscle-info">{{ m.muscle }}</div>
            
            <div class="section-title">איך לבצע:</div>
            <div class="guide-info">{{ m.guide }}</div>
            
            <iframe src="{{ m.video_url }}" allowfullscreen></iframe>
            
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
                        <span>{{ h[0] }} ק״ג x {{ h[1] }} חזרות</span>
                        <span>{{ h[2][:16] }}</span>
                    </div>
                    {% endfor %}
                {% else %}
                    <span>טרם נרשמו אימונים למכונה זו</span>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        let currentCategory = 'הכל';

        function toggleTheme() {
            document.body.classList.toggle('light-mode');
        }

        function setCategory(cat, btn) {
            currentCategory = cat;
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterMachines();
        }

        function filterMachines() {
            const query = document.getElementById('searchBox').value.toLowerCase();
            const cards = document.querySelectorAll('.machine-card');

            cards.forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const category = card.getAttribute('data-category');
                const matchesSearch = name.includes(query);
                const matchesCat = (currentCategory === 'הכל' || category === currentCategory);

                if (matchesSearch && matchesCat) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        async function saveWeight(e, machineId) {
            e.preventDefault();
            const weight = document.getElementById(`weight-${machineId}`).value;
            const reps = document.getElementById(`reps-${machineId}`).value;

            const res = await fetch('/api/add_weight', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({machine_id: machineId, weight: parseFloat(weight), reps: parseInt(reps)})
            });

            if(res.ok) {
                const data = await res.json();
                const historyBox = document.getElementById(`history-${machineId}`);
                
                // אם זו ההיסטוריה הראשונה, נקה את הודעת הטרם נרשמו
                if(historyBox.innerHTML.includes('טרם נרשמו')) {
                    historyBox.innerHTML = '';
                }

                const newItem = document.createElement('div');
                newItem.className = 'history-item';
                newItem.innerHTML = `<span>${data.weight} ק״ג x ${data.reps} חזרות</span><span>${data.date.substring(0,16)}</span>`;
                historyBox.prepend(newItem);

                document.getElementById(`weight-${machineId}`).value = '';
                document.getElementById(`reps-${machineId}`).value = '';
            }
        }
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
    conn.close()

    history = {}
    for r in rows:
        m_id, w, reps, d = r[0], r[1], r[2], r[3]
        if m_id not in history:
            history[m_id] = []
        history[m_id].append((w, reps, d))

    return render_template_string(HTML_TEMPLATE, machines=MACHINES, history=history)

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
    cursor.execute("SELECT datetime('now', '+3 hours')") # שעון ישראל
    date_str = cursor.fetchone()[0]
    conn.close()

    return jsonify({"success": True, "weight": weight, "reps": reps, "date": date_str})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)