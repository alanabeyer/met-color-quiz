from flask import Flask, render_template, request, redirect
import requests
import random
from PIL import Image
from io import BytesIO
import colorsys


app = Flask(__name__)

def fetch_paintings():
    url = 'https://collectionapi.metmuseum.org/public/collection/v1/search'
    params = {
        'q': 'paintings',
        'hasImages': 'true',
        'medium': 'Paintings'
    }
    response = requests.get(url, params=params)
    data = response.json()
    paintings = data['objectIDs']
    return paintings

def fetch_painting_data(painting_id):
    url = f'https://collectionapi.metmuseum.org/public/collection/v1/objects/{painting_id}'
    response = requests.get(url)
    data = response.json()
    return data


import requests
from PIL import Image
from io import BytesIO
import colorsys

import numpy as np
from sklearn.cluster import KMeans

def extract_color_palette(image_url, num_colors=10, small_image_size=(200, 200),
                          brightness_threshold=0.2, saturation_threshold=0.2):
    try:
        # Download the image from the URL
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        # Resize the image for faster processing (optional)
        image = image.resize((1000, 1000))

        # Convert the image to the RGB color mode
        image = image.convert("RGB")

        # Resize the image to a larger size for color analysis
        small_image = image.resize(small_image_size)

        # Get the pixel colors from the small image
        pixels = np.array(small_image)

        # Flatten the pixel array
        pixels = pixels.reshape(-1, 3)

        # Convert the RGB pixel values to HLS color space
        hls_pixels = [colorsys.rgb_to_hls(r / 255, g / 255, b / 255) for r, g, b in pixels]

        # Filter the pixels based on brightness and saturation thresholds
        filtered_pixels = [pixel for pixel in hls_pixels if pixel[1] > brightness_threshold and pixel[2] > saturation_threshold]

        # Extract the HLS values from the filtered pixels
        hls_values = np.array([[pixel[0], pixel[1], pixel[2]] for pixel in filtered_pixels])

        # Perform K-means clustering to group similar colors together
        kmeans = KMeans(n_clusters=num_colors, random_state=42).fit(hls_values)

        # Get the cluster centers which represent the dominant colors
        cluster_centers = kmeans.cluster_centers_

        # Convert the HLS color values to RGB color values
        rgb_colors = [colorsys.hls_to_rgb(center[0], center[1], center[2]) for center in cluster_centers]

        # Convert the RGB color values to hexadecimal format
        color_palette = [f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}" for r, g, b in rgb_colors]

        return color_palette
    except:
        return []  # Return an empty color palette in case of any error



def get_random_painters(painting_data, num_options=4):
    all_painters = [painting_data['artistDisplayName']]
    while len(all_painters) < num_options:
        random_painting = random.choice(fetch_paintings())
        random_painting_data = fetch_painting_data(random_painting)
        if 'artistDisplayName' in random_painting_data:
            painter = random_painting_data['artistDisplayName']
            if painter not in all_painters:
                all_painters.append(painter)
    random.shuffle(all_painters)
    return all_painters



@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_guess = request.form['guess']
        painting_id = request.form['painting_id']
        painting_data = fetch_painting_data(painting_id)
        actual_artist = painting_data['artistDisplayName']
        color_palette = extract_color_palette(painting_data['primaryImage'])
        painters = get_random_painters(painting_data)
        painting_image_url = painting_data['primaryImage']

        if user_guess.lower() == actual_artist.lower():
            result = "Correct!"
        else:
            result = f"Incorrect. The artist is {actual_artist}."

        return render_template('result.html', result=result, palette=color_palette,
                               painters=painters, painting_id=painting_id,
                               painting_image_url=painting_image_url)
    
    # GET request
    paintings = fetch_paintings()
    painting_id = random.choice(paintings)
    painting_data = fetch_painting_data(painting_id)
    
    if 'primaryImage' in painting_data:
        color_palette = extract_color_palette(painting_data['primaryImage'])
        painters = get_random_painters(painting_data)
        return render_template('game.html', palette=color_palette, painters=painters, painting_id=painting_id)
    else:
        # Handle the case where the 'primaryImage' key is not present in painting_data
        return redirect('/')  # Redirect to the home route to try again


@app.route('/guess', methods=['POST'])
def guess():
    user_guess = request.form['guess']
    painting_id = request.form['painting_id']
    painting_data = fetch_painting_data(painting_id)
    actual_artist = painting_data['artistDisplayName']
    color_palette = extract_color_palette(painting_data['primaryImage'])
    painters = get_random_painters(painting_data)
    painting_image_url = painting_data['primaryImage']

    if user_guess.lower() == actual_artist.lower():
        result = "Correct!"
    else:
        result = f"Incorrect. The artist is {actual_artist}."

    return render_template('result.html', result=result, palette=color_palette,
                           painters=painters, painting_id=painting_id,
                           painting_image_url=painting_image_url)


if __name__ == '__main__':
    app.run()

