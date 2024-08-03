import base64
from flask import Flask, jsonify, request, render_template
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
import os
from io import BytesIO
import uuid
from PIL import Image
from datetime import datetime

from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

app = Flask(__name__, template_folder='static')

# Retrieve environment variables
vision_endpoint = os.environ["VISION_ENDPOINT"]
vision_key = os.environ["VISION_KEY"]
openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
openai_api_key = os.environ["AZURE_OPENAI_API_KEY"]
imagekit_private_key = os.environ["IMAGEKIT_PRIVATE_KEY"]
imagekit_public_key = os.environ["IMAGEKIT_PUBLIC_KEY"]
imagekit_url_endpoint = os.environ["IMAGEKIT_URL_ENDPOINT"]

vision_client = ImageAnalysisClient(
    endpoint=vision_endpoint,
    credential=AzureKeyCredential(vision_key)
)

openai_client = AzureOpenAI(
    api_key=openai_api_key,
    api_version="2024-02-01",
    azure_endpoint=openai_endpoint
)

imagekit = ImageKit(
    private_key=imagekit_private_key,
    public_key=imagekit_public_key,
    url_endpoint = imagekit_url_endpoint
)

imagekit_options = UploadFileRequestOptions(
    use_unique_file_name=False,
    is_private_file=False,
    overwrite_file=True,
    overwrite_ai_tags=False,
    overwrite_tags=False,
    overwrite_custom_metadata=True,
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
        prompt = f"""Generate a recipe in HTML format with Tailwind CSS classes for styling. Use a main `div` with the class `recipe-container`, which should have a semi-transparent background (`bg-gray-800 bg-opacity-50`), rounded corners (`rounded-lg`), padding (`p-6`), and a shadow effect (`shadow-lg`). The recipe title should be an `h3` with the class `recipe-title`, styled with `text-4xl`, `font-bold`, and `text-white`. The recipe instructions should be in a `p` tag with the class `recipe-text`, styled with `text-lg` and `text-white`. Ensure the design is clean, modern, and readable against a dark background. Here are the ingredients: {', '.join(ingredients)}.
        
        Sample structure:
        <div class="recipe-container bg-gray-800 bg-opacity-50 rounded-lg p-6 shadow-lg">
            <h3 class="recipe-title text-4xl font-bold text-white">Recipe Title</h3>
            <p class="recipe-text text-lg text-white">
                <ul>
                    <li>Recipe Ingredients (With quantity)...</li>
                </ul>
                <ul>
                    <li>Recipe instructions...</li>
                </ul>
            </p>
        </div>
        
        """
        
        try:
            response = openai_client.completions.create(
                model=deployment_name,
                prompt=prompt,
                max_tokens=300
            )
            recipe = response.choices[0].text.strip()

            print(recipe)

            return jsonify({"recipe": recipe})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_image():
    data = request.get_json()
    
    if 'image' not in data:
        return jsonify({"error": "No image data"}), 400

    image_data = data['image']
    
    try:
        # Remove the data URL scheme if present
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        # Decode the base64 image data
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Ensure the image is in PNG format
        if image.format != 'PNG':
            image = image.convert('RGB')
            # filename = str(uuid.uuid4()) + '.jpg'
            filename = "image.jpg"
        else:
            # filename = str(uuid.uuid4()) + '.png'
            filename = "image.png"
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        image.save(file_path, format='PNG' if image.format == 'PNG' else 'JPEG')

        # Upload the image to ImageKit
        with open(file_path, 'rb') as file:
            imagekit.upload(file, file_name=filename, options=imagekit_options)
        
        file_url = f'{imagekit_url_endpoint}/{filename}'
        
        return jsonify({"url": file_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    data = request.json
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({"error": "Missing 'image_url' in request"}), 400

    # Append a unique query parameter to avoid caching issues
    unique_url = f"{image_url}?t={datetime.now().timestamp()}"

    try:
        result = vision_client.analyze_from_url(
            image_url=unique_url,
            visual_features=[VisualFeatures.READ]
        )

        # Process the extracted text
        ingredients_text = ""
        if result.read:
            for block in result.read.blocks:
                for line in block.lines:
                    ingredients_text += line.text + "\n"

        # Parse text into a list of ingredients
        ingredients = ingredients_text.split('\n')
        ingredients = [ingredient.strip() for ingredient in ingredients if ingredient.strip()]

        return jsonify({"ingredients": ingredients})

    except Exception as e:
        print("Exception:", str(e))
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
