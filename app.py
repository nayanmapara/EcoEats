from flask import Flask, jsonify, request, render_template, send_from_directory
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import os

import uuid

app = Flask(__name__, template_folder='static')

# Retrieve environment variables
vision_endpoint = os.environ["VISION_ENDPOINT"]
vision_key = os.environ["VISION_KEY"]
openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
openai_api_key = os.environ["AZURE_OPENAI_API_KEY"]

vision_client = ImageAnalysisClient(
    endpoint=vision_endpoint,
    credential=AzureKeyCredential(vision_key)
)

openai_client = AzureOpenAI(
    api_key=openai_api_key,
    api_version="2024-02-01",
    azure_endpoint=openai_endpoint
)

deployment_name = 'baseMod'  # Your GPT-35-turbo-instruct deployment name
UPLOAD_FOLDER = './static/assets/imgs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/capture')
def upload_page():
    return render_template('capture.html')

@app.route('/recipe', methods=['GET', 'POST'])
def recipe_page():
    if request.method == 'GET':
        # Render the page where users will see the ingredients and recipe
        ingredients = request.args.getlist('ingredients')
        if not ingredients:
            return "No ingredients provided", 400
        return render_template('recipe.html', ingredients=ingredients)
    
    if request.method == 'POST':
        # Handle recipe generation
        data = request.json
        ingredients = data.get('ingredients', [])
        
        if not ingredients:
            return jsonify({"error": "No ingredients provided"}), 400
        
        # Create a prompt for the OpenAI API
        prompt = f"Generate a recipe based on the following ingredients: {', '.join(ingredients)}"
        
        try:
            response = openai_client.completions.create(
                model=deployment_name,
                prompt=prompt,
                max_tokens=150
            )
            recipe = response.choices[0].text.strip()
            return jsonify({"recipe": recipe})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
        # Generate a unique filename
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        file.save(file_path)
        
        # Construct the URL (assuming the app is running on localhost:5000)
        file_url = f'/imgs/{filename}'
        
        # Optionally delete the file after processing
        # os.remove(file_path)
        
        return jsonify({"url": file_url})
    
    return jsonify({"error": "Invalid file format"}), 400

@app.route('/imgs/<filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    data = request.json
    image_url = data.get('image_url')
    
    if not image_url:
        return jsonify({"error": "Missing 'image_url' in request"}), 400

    try:
        result = vision_client.analyze_from_url(
            image_url=image_url,
            visual_features=[VisualFeatures.READ]
        )
        
        # Process the extracted text
        ingredients_text = ""
        if result.read:
            for block in result.read.blocks:
                for line in block.lines:
                    ingredients_text += line.text + "\n"
        
        # Optionally delete the file after processing
        # os.remove(file_path)

        # Parse text into a list of ingredients
        ingredients = ingredients_text.split('\n')
        ingredients = [ingredient.strip() for ingredient in ingredients if ingredient.strip()]

        return jsonify({"ingredients": ingredients})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/generate_recipe', methods=['POST'])
def generate_recipe():
    data = request.json
    ingredients = data.get('ingredients')

    if not ingredients or not isinstance(ingredients, list):
        return jsonify({"error": "Missing or invalid 'ingredients' in request"}), 400

    ingredients_text = ", ".join(ingredients)
    prompt = f"Write a recipe using the following ingredients: {ingredients_text}"

    try:
        response = openai_client.completions.create(
            model=deployment_name,
            prompt=prompt,
            max_tokens=150
        )
        recipe_text = response.choices[0].text.strip()
        return jsonify({"recipe": recipe_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
