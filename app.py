from flask import Flask, render_template, request, send_file
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
import matplotlib.pyplot as plt
import io
import os

app = Flask(_name_)

# Load dataset
file_path = "large_allergen_food_dataset.csv"
df = pd.read_csv(file_path)

# Allergen and alternative mappings
allergen_mapping = { "Milk": "Dairy", "Paneer": "Dairy", "Cream": "Dairy", "Butter": "Dairy", "Yogurt": "Dairy", "Cheese": "Dairy", "Ghee": "Dairy", "Egg": "Eggs", "Wheat": "Gluten", "Flour": "Gluten", "Noodles": "Gluten", "Bread": "Gluten", "Maida": "Gluten", "Soy": "Soy", "Soy Sauce": "Soy", "Tofu": "Soy", "Edamame": "Soy", "Miso": "Soy", "Peanuts": "Peanuts", "Groundnut": "Peanuts", "Almonds": "Tree Nuts", "Cashews": "Tree Nuts", "Walnuts": "Tree Nuts", "Hazelnuts": "Tree Nuts", "Fish": "Fish", "Shrimp": "Shellfish", "Lobster": "Shellfish", "Crab": "Shellfish", "Sesame": "Sesame", "Sesame Oil": "Sesame", "Tahini": "Sesame", "Mustard": "Mustard", "Lupin": "Lupin" }

alternative_mapping = { "Dairy": "Almond milk, Oat milk, Coconut milk, Vegan cheese", "Eggs": "Flaxseed egg, Chia egg, Applesauce", "Gluten": "Rice flour, Quinoa flour, Chickpea flour", "Soy": "Coconut aminos, Chickpeas, Lentils", "Peanuts": "Sunflower seed butter, Pumpkin seed butter", "Tree Nuts": "Sunflower seeds, Pumpkin seeds", "Fish": "Jackfruit, Plant-based seafood", "Shellfish": "Plant-based seafood, Mushrooms", "Sesame": "Sunflower butter, Pumpkin seeds", "Mustard": "Turmeric, Mustard-free dressings", "Lupin": "Rice flour, Chickpea flour" }

# Function to detect allergens
def detect_allergens(ingredients):
    detected = set()
    for ingredient, allergen in allergen_mapping.items():
        if ingredient.lower() in ingredients.lower():
            detected.add(allergen)
    return ", ".join(detected) if detected else "None"

# Function to get alternative suggestions
def suggest_alternatives(detected_allergens):
    allergens = detected_allergens.split(", ")
    alternatives = [alternative_mapping.get(a, "No alternative available") for a in allergens]
    return ", ".join(alternatives) if alternatives else "No alternatives available"

# Function to generate pie chart
def generate_pie_chart(detected_allergens):
    labels = detected_allergens.split(", ") if detected_allergens != "None" else []
    sizes = [1] * len(labels)
    
    plt.figure(figsize=(5, 5))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=plt.cm.Paired.colors)
    plt.title("Allergen Distribution")
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    return buffer

# Function to generate PDF
def generate_pdf(food_name, ingredients, detected_allergens, alternatives, notes):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    pdf.drawString(100, 750, f"Food Name: {food_name}")
    pdf.drawString(100, 730, f"Ingredients: {ingredients}")
    pdf.drawString(100, 710, f"Detected Allergens: {detected_allergens}")
    pdf.drawString(100, 690, f"Alternative Suggestions: {alternatives}")
    pdf.drawString(100, 670, f"Notes: {notes}")
    
    # Generate and insert pie chart at a dedicated space
    if detected_allergens != "None":
        pie_chart = generate_pie_chart(detected_allergens)
        chart_path = "temp_pie_chart.png"
        with open(chart_path, "wb") as f:
            f.write(pie_chart.getbuffer())
        pdf.drawImage(chart_path, 150, 300, width=300, height=300)  # Adjusted position
        os.remove(chart_path)
    
    pdf.save()
    buffer.seek(0)
    return buffer

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        food_name = request.form.get("food_name")
        food_item = df[df["Food Name"].str.lower() == food_name.lower()]
        
        if food_item.empty:
            result = {"error": f"Food item '{food_name}' not found."}
        else:
            ingredients = food_item["Ingredients"].values[0]
            detected_allergens = detect_allergens(ingredients)
            alternatives = suggest_alternatives(detected_allergens)
            notes = f"⚠ Contains {detected_allergens}. Avoid if allergic." if detected_allergens != "None" else "✅ Safe to consume."
            
            result = {
                "food_name": food_name,
                "ingredients": ingredients,
                "detected_allergens": detected_allergens,
                "alternatives": alternatives,
                "notes": notes
            }
    
    return render_template("index.html", result=result)

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    food_name = request.form.get("food_name")
    food_item = df[df["Food Name"].str.lower() == food_name.lower()]
    
    if food_item.empty:
        return "Food item not found", 404
    
    ingredients = food_item["Ingredients"].values[0]
    detected_allergens = detect_allergens(ingredients)
    alternatives = suggest_alternatives(detected_allergens)
    notes = f"⚠ Contains {detected_allergens}. Avoid if allergic." if detected_allergens != "None" else "✅ Safe to consume."
    
    pdf_buffer = generate_pdf(food_name, ingredients, detected_allergens, alternatives, notes)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"{food_name}_report.pdf", mimetype="application/pdf")

if _name_ == "_main_":
    app.run(debug=True)
