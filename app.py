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

# מאגר תרגילים מורחב הכולל קישורים לתמונות אנטומיות ייעודיות לכל שריר
MACHINES = {
    # --- חזה ---
    "bench_press": {
        "name": "לחיצת חזה מוט (שטוח)", "category": "חזה", "type": "free", 
        "muscle": "חזה גדול, יד אחורית, כתף קדמית", "guide": "שכוב על הספסל, אחוז מוט ברוחב כתפיים, הורד לשד ודחף למעלה.", 
        "video_url": "https://www.youtube.com/embed/rT7DgCr-3pg",
        "anatomy_img": "https://exrx.net/Muscles/PectoralisSternal.jpg"
    },
    "incline_bench": {
        "name": "לחיצת חזה מוט בשיפוע עליון", "category": "חזה", "type": "free", 
        "muscle": "חזה עליון", "guide": "ספסל בשיפוע של 30-45 מעלות, דחף את המוט כלפי מעלה.", 
        "video_url": "https://www.youtube.com/embed/SrqNv9yexnY",
        "anatomy_img": "https://exrx.net/Muscles/PectoralisClavicular.jpg"
    },
    "dumbbell_press": {
        "name": "לחיצת חזה עם דאמבלים", "category": "חזה", "type": "free", 
        "muscle": "חזה גדול ומייצבים", "guide": "החזק משקולות חופשיות ודחף מעלה תוך קירוב קל למעלה.", 
        "video_url": "https://www.youtube.com/embed/VmB1G1K7v94",
        "anatomy_img": "https://exrx.net/Muscles/PectoralisSternal.jpg"
    },
    "chest_press_machine": {
        "name": "לחיצת חזה במכונה", "category": "חזה", "type": "machine", 
        "muscle": "חזה גדול", "guide": "שב בצמוד למשענת ודחף את הידיות לפנים.", 
        "video_url": "https://www.youtube.com/embed/sqOw2Y6uDWQ",
        "anatomy_img": "https://exrx.net/Muscles/PectoralisSternal.jpg"
    },
    "pec_fly": {
        "name": "פרפר / קירוב חזה", "category": "חזה", "type": "machine", 
        "muscle": "חזה מבודד", "guide": "שמור מרפקים מעט קבועים וקרב את הידיים זו לזו.", 
        "video_url": "https://www.youtube.com/embed/Z57CtZuYxug",
        "anatomy_img": "https://exrx.net/Muscles/PectoralisSternal.jpg"
    },

    # --- גב ---
    "pullups": {
        "name": "מתח (Pull-ups)", "category": "גב", "type": "free", 
        "muscle": "רחב גבי (Lats), יד קדמית", "guide": "תפוס אחיזה רחבה ומשוך את החזה אל המוט.", 
        "video_url": "https://www.youtube.com/embed/eGo4IYlbE5g",
        "anatomy_img": "https://exrx.net/Muscles/LatissimusDorsi.jpg"
    },
    "lat_pulldown": {
        "name": "פולי עליון רחב", "category": "גב", "type": "machine", 
        "muscle": "רחב גבי", "guide": "משוך את המוט אל החזה העליון תוך הוצאת חזה.", 
        "video_url": "https://www.youtube.com/embed/CAwf7n6Luuc",
        "anatomy_img": "https://exrx.net/Muscles/LatissimusDorsi.jpg"
    },
    "barbell_row": {
        "name": "חתירה במוט בהטיית גו", "category": "גב", "type": "free", 
        "muscle": "גב אמצעי, רחב גבי", "guide": "התכופף עם גב ישיר ומשוך את המוט אל הבטן.", 
        "video_url": "https://www.youtube.com/embed/GWD8lV23IB4",
        "anatomy_img": "https://exrx.net/Muscles/TrapeziusMiddle.jpg"
    },
    "seated_row": {
        "name": "חתירה בישיבה (פולי תחתון)", "category": "גב", "type": "machine", 
        "muscle": "גב אמצעי", "guide": "משוך את הידיות לטבור והדק שכמות מאחור.", 
        "video_url": "https://www.youtube.com/embed/GZbfZ033fBo",
        "anatomy_img": "https://exrx.net/Muscles/TrapeziusMiddle.jpg"
    },
    "deadlift": {
        "name": "דדליפט (Deadlift)", "category": "גב", "type": "free", 
        "muscle": "גב תחתון, המסטרינג, ישבן", "guide": "הרים מוט מהרצפה תוך שמירה על גב ישר לגמרי.", 
        "video_url": "https://www.youtube.com/embed/op9kVnSso6Q",
        "anatomy_img": "https://exrx.net/Muscles/ErectorSpinae.jpg"
    },

    # --- רגליים ---
    "squat": {
        "name": "סקוואט חופשי עם מוט", "category": "רגליים", "type": "free", 
        "muscle": "ארבע-ראשי, ישבן, ליבה", "guide": "הנח מוט על הטרפזים, רד לעומק בשליטה ועלייה.", 
        "video_url": "https://www.youtube.com/embed/ultWZbUMPL8",
        "anatomy_img": "https://exrx.net/Muscles/Quadriceps.jpg"
    },
    "leg_press": {
        "name": "לחיצת רגליים (Leg Press)", "category": "רגליים", "type": "machine", 
        "muscle": "ארבע-ראשי וישבן", "guide": "דחף את הפלטפורמה בלי לנעול לגמרי ברכיים.", 
        "video_url": "https://www.youtube.com/embed/IZxyjW7MPJQ",
        "anatomy_img": "https://exrx.net/Muscles/Quadriceps.jpg"
    },
    "leg_extension": {
        "name": "פשטת ברכיים (ירך קדמית)", "category": "רגליים", "type": "machine", 
        "muscle": "ארבע-ראשי (Quadriceps)", "guide": "ישר את הרגליים קדימה במכונה ייעודית.", 
        "video_url": "https://www.youtube.com/embed/YyvSfVjQeL0",
        "anatomy_img": "https://exrx.net/Muscles/Quadriceps.jpg"
    },
    "leg_curl": {
        "name": "כפיפת ברכיים (ירך אחורית)", "category": "רגליים", "type": "machine", 
        "muscle": "המסטרינג (Hamstrings)", "guide": "כופף את הרגליים לאחור כנגד ההתנגדות.", 
        "video_url": "https://www.youtube.com/embed/1T5Kjn7x91w",
        "anatomy_img": "https://exrx.net/Muscles/Hamstrings.jpg"
    },
    "calf_raise": {
        "name": "הרים שוקיים / תאומים", "category": "רגליים", "type": "machine", 
        "muscle": "שוקיים (Calves)", "guide": "עלה על קצות האצבעות והורד עקבים למטה למתיחה.", 
        "video_url": "https://www.youtube.com/embed/YMme0n7Bedw",
        "anatomy_img": "https://exrx.net/Muscles/Gastrocnemius.jpg"
    },

    # --- כתפיים ---
    "overhead_press": {
        "name": "לחיצת כתפיים עמידה במוט", "category": "כתפיים", "type": "free", 
        "muscle": "כתף קדמית ואמצעית", "guide": "דחף את המוט מעל הראש ממצב חזה.", 
        "video_url": "https://www.youtube.com/embed/2yjwXT8jOPw",
        "anatomy_img": "https://exrx.net/Muscles/DeltoidAnterior.jpg"
    },
    "lateral_raise": {
        "name": "הרחקת כתפיים לצדדים בדאמבלים", "category": "כתפיים", "type": "free", 
        "muscle": "כתף אמצעית", "guide": "הרים דאמבלים לצדדים עד בגובה הכתף.", 
        "video_url": "https://www.youtube.com/embed/3VcKaXpzqRo",
        "anatomy_img": "https://exrx.net/Muscles/DeltoidLateral.jpg"
    },

    # --- ידיים ---
    "biceps_curl": {
        "name": "כפיפת מרפקים (יד קדמית)", "category": "ידיים", "type": "free", 
        "muscle": "יד קדמית (Biceps)", "guide": "הקפד לא לזוז עם הגב והרם את המשקל למעלה.", 
        "video_url": "https://www.youtube.com/embed/ykJmrZ5v0Oo",
        "anatomy_img": "https://exrx.net/Muscles/BicepsBrachii.jpg"
    },
    "triceps_pushdown": {
        "name": "פשיטת מרפקים בפולי (יד אחורית)", "category": "ידיים", "type": "machine", 
        "muscle": "יד אחורית (Triceps)", "guide": "דחף את החבל או המוט כלפי מטה עם מרפקים צמודים לגוף.", 
        "video_url": "https://www.youtube.com/embed/2-w9bqa5t1s",
        "anatomy_img": "https://exrx.net/Muscles/TricepsBrachii.jpg"
    },

    # --- בטן ---
    "crunch": {
        "name": "כפיפות בטן", "category": "בטן", "type": "machine", 
        "muscle": "שרירי הבטן הישירים", "guide": "כופף את פלג הגוף העליון קדימה בכיוון האגן.", 
        "video_url": "https://www.youtube.com/embed/MKiuj6A4Hcs",
        "anatomy_img": "https://exrx.net/Muscles/RectusAbdominis.jpg"
    }
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
        
        .filters, .type-filters { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 5px; }
        .filter-btn { background: var(--card-bg); color: var(--text-color); border: 1px solid var(--border); padding: 6px 12px; border-radius: 20px; font-size: 13px; cursor: pointer; white-space: nowrap; }
        .filter-btn.active { background: var(--accent); color: #000; border-color: var(--accent); font-weight: bold; }

        .machine-card { background-color: var(--card-bg); border-radius: 12px; padding: 16px; margin-bottom: 15px; border: 1px solid var(--border); }
        .machine-title { font-size: 18px; font-weight: bold; color: var(--accent); }
        .badge-group { display: flex; gap: 5px; margin-top: 5px; }
        .badge { display: inline-block; background: var(--input-bg); color: var(--subtext); padding: 3px 8px; border-radius: 6px; font-size: 11px; }
        
        .content-grid { display: grid; grid-template-columns: 1fr 120px; gap: 10px; align-items: center; margin-top: 10px; }
        .anatomy-img { width: 100%; height: 120px; object-fit: contain; background: #fff; border-radius: 8px; padding: 4px; border: 1px solid var(--border); }
        
        .section-title { font-size: 13px; color: var(--subtext); margin-top: 10px; }
        .muscle-info { font-size: 14px; color: var(--text-color); margin-bottom: 6px; }
        .guide-info { font-size: 13px; color: var(--subtext); line-height: 1.4; margin-bottom: 10px; }
        iframe { width: 100%; height: 180px; border-radius: 8px; border: none; margin-bottom: 12px; margin-top: 10px; }
        
        .form-group { display: flex; gap: 8px; margin-top: 10px; }
        input[type="number"] { flex: 1; padding: 10px; background: var(--input-bg); border: 1px solid var(--border); color: var(--text-color); border-radius: 8px; font-size: 14px; text-align: center; }
        button.save-btn { background-color: var(--accent); color: #000; border: none; padding: 10px 15px; font-weight: bold; border-radius: 8px; cursor: pointer; }
        
        .history-box { margin-top: 12px; background: var(--input-bg); padding: 10px; border-radius: 8px; font-size: 12px; max-height: 120px; overflow-y: auto; color: var(--subtext); }
        .history-item { display: flex; justify-content: space-between; border-bottom: 1px solid var(--border); padding: 4px 0; }
    </style>
</head>
<body>
    <header>
        <h1>GymLog Pro 🏋️‍♂️</h1>
        <button class="theme-btn" onclick="toggleTheme()">🌓 מצב תצוגה</button>
    </header>

    <div class="controls">
        <input type="text" id="searchBox" class="search-box" placeholder="חפש תרגיל או מכונה..." oninput="filterMachines()">
        
        <div class="type-filters">
            <button class="filter-btn active" onclick="setType('all', this)">הכל</button>
            <button class="filter-btn" onclick="setType('free', this)">🏋️ משקל חופשי</button>
            <button class="filter-btn" onclick="setType('machine', this)">🦾 מכונות</button>
        </div>

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
        <div class="machine-card" data-name="{{ m.name }}" data-category="{{ m.category }}" data-type="{{ m.type }}">
            <div class="machine-title">{{ m.name }}</div>
            <div class="badge-group">
                <span class="badge">{{ m.category }}</span>
                <span class="badge">{% if m.type == 'free' %}משקל חופשי{% else %}מכונה{% endif %}</span>
            </div>
            
            <div class="content-grid">
                <div>
                    <div class="section-title">שרירים פועלים:</div>
                    <div class="muscle-info">{{ m.muscle }}</div>
                </div>
                <div>
                    <img src="{{ m.anatomy_img }}" alt="שריר מטרה" class="anatomy-img" title="השריר המרכזי שעובדים עליו">
                </div>
            </div>
            
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
                        <span><strong>{{ h[0] }} ק״ג</strong> x {{ h[1] }} חזרות</span>
                        <span>{{ h[2][:16] }}</span>
                    </div>
                    {% endfor %}
                {% else %}
                    <span>טרם נרשמו אימונים לתרגיל זה</span>
                {% endif %}
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        let currentCategory = 'הכל';
        let currentType = 'all';

        function toggleTheme() {
            document.body.classList.toggle('light-mode');
        }

        function setCategory(cat, btn) {
            currentCategory = cat;
            document.querySelectorAll('.filters .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterMachines();
        }

        function setType(type, btn) {
            currentType = type;
            document.querySelectorAll('.type-filters .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterMachines();
        }

        function filterMachines() {
            const query = document.getElementById('searchBox').value.toLowerCase();
            const cards = document.querySelectorAll('.machine-card');

            cards.forEach(card => {
                const name = card.getAttribute('data-name').toLowerCase();
                const category = card.getAttribute('data-category');
                const type = card.getAttribute('data-type');

                const matchesSearch = name.includes(query);
                const matchesCat = (currentCategory === 'הכל' || category === currentCategory);
                const matchesType = (currentType === 'all' || type === currentType);

                if (matchesSearch && matchesCat && matchesType) {
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
                
                if(historyBox.innerHTML.includes('טרם נרשמו')) {
                    historyBox.innerHTML = '';
                }

                const newItem = document.createElement('div');
                newItem.className = 'history-item';
                newItem.innerHTML = `<span><strong>${data.weight} ק״ג</strong> x ${data.reps} חזרות</span><span>${data.date.substring(0,16)}</span>`;
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
