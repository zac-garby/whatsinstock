from flask import Flask, send_from_directory, request, redirect

app = Flask(__name__)

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/submit', methods=['POST'])
def submit():
    # Get the form data
    fat = request.form.get('fat')
    saturated_fat = request.form.get('saturatedFat')
    carbs = request.form.get('carbs')
    sugars = request.form.get('sugars')
    fiber = request.form.get('fiber')
    protein = request.form.get('protein')
    sodium = request.form.get('sodium')

    print(f'Fat: {fat}, Saturated Fat: {saturated_fat}, Carbs: {carbs}, Sugars: {sugars}, Fiber: {fiber}, Protein: {protein}, Sodium: {sodium}')
    
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
