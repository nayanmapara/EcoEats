# EcoEats

EcoEats is a web app designed to help users reduce food waste by providing recipes based on the ingredients they have by analyzing photos of the list of items in thier fridge or pantry. EcoEats generates personalized recipe suggestions to help you make the most out of what you have.

## Features

- **Photo-based Ingredient Extraction**: Upload a photo of the list of items in your fridge and let EcoEats extract the items.
- **Recipe Generation**: Receive tailored recipes based on the ingredients detected.
- **Sustainable Living**: Reduce food waste and contribute to a more eco-friendly lifestyle.
- **Modern User Interface**: Enjoy a clean and intuitive design built with Tailwind CSS.

## Technologies Used

- **Frontend**: HTML, JavaScript, Tailwind CSS
- **Backend**: Python, Flask, Azure API Integration
- **Cloud & DevOps**: Azure, Vercel
- **Other Tools**: Azure Vision AI, Azure OpenAI API

## Getting Started

### Prerequisites

- A modern web browser (e.g., Chrome, Firefox)
- Python (v3.8 or higher) for backend
- An Azure account for API integrations

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/nayanmapara/EcoEats
    cd EcoEats
   ```

2. **Set Up the Backend**

   Navigate to the `backend` directory and install dependencies:

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

   Set up environment variables in a `.env` file in the `backend` directory.

3. **Run the Application**

   ```bash
    python app.py
    ```

### Usage

1. Open the EcoEats web application in your browser.
2. Upload a photo of a the list of items in your fridge or pantry.
3. The app will process the image and extract the ingredients.
4. View personalized recipe suggestions based on the detected ingredients.

---

Thank you for checking out EcoEats! We hope it helps you make the most out of your ingredients and contributes to a more sustainable lifestyle.
