import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request
from lib.waveshare_epd import epd2in15g 

app = Flask(__name__)
last_printed_message = None

try:
    epd = epd2in15g.EPD()
    epd.init()
    epd.Clear()

    # Load system font with safety fallback
    try:
        system_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
    except OSError:
        system_font = ImageFont.load_default()

    # ==========================================
    # STEP 1: RENDER AND DISPLAY FIRST TEXT
    # ==========================================
    print("Preparing Frame 1...")
    
    # Create canvas with REVERSED dimensions (Height x Width) for portrait design
    canvas1 = Image.new('1', (epd.height, epd.width), 255)
    draw1 = ImageDraw.Draw(canvas1)
    draw1.text((10, 30), "Du Penis", font=system_font, fill=0)     # Draw text onto the portrait canvas
    rotated_canvas1 = canvas1.rotate(90, expand=True) # Rotate the canvas 90 degrees to fit the landscape hardware screen
    print("Refreshing Screen (Blinking will take ~20 seconds)...")
    epd.display(epd.getbuffer(rotated_canvas1))
    print("Frame 1 Complete.")
    print("Finalizing updates. Putting display to sleep...")
    epd.sleep()
    print("Finished successfully!")

except Exception as e:
    print(f"Error encountered: {e}")

@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template(
        'index.html',
        printed_message=None,
        last_printed=last_printed_message
    )


@app.route('/print', methods=['POST'])
def print_message():

    global last_printed_message
    
    # Get the message from the form
    message = request.form.get('message', 'Hello World')
    
    # Print to CLI
    print(f"Printed: {message}")
    """try:
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas1)
        draw.text((10, 30), {message}, font=system_font, fill=0)     # Draw text onto the portrait canvas
        rotated_canvas1 = canvas1.rotate(90, expand=True) # Rotate the canvas 90 degrees to fit the landscape hardware screen
        print("Refreshing Screen (Blinking will take ~20 seconds)...")
        epd.display(epd.getbuffer(rotated_canvas1))
        epd.sleep()
    except Exception as e:
        print(f"Error encountered: {e}")"""

    # Store the last printed message
    #last_printed_message = message
    
    # Render the template with success message
    return render_template(
        'index.html',
        printed_message=message,
        last_printed=last_printed_message
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
