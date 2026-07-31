import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request

app = Flask(__name__)

# Try to import the waveshare e-paper library
try:
    from lib.waveshare_epd import epd2in15g
    EPD_AVAILABLE = True
except ImportError:
    EPD_AVAILABLE = False
    print("Warning: Waveshare e-paper library not available")


@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template('index.html', printed_message=None)


def display_on_epaper(message):
    from lib.waveshare_epd import epd2in15g 

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

        print("Waiting 25 seconds...")
        time.sleep(25)
        print("Preparing Frame 2...")
        canvas2 = Image.new('1', (epd.height, epd.width), 255)
        draw2 = ImageDraw.Draw(canvas2)
        lines = [
            "Keep going,",
            "Keep Working",
            "You got this!",
            "Stay strong!"
        ]
        
        y_position = 30
        for line in lines:
            draw2.text((10, y_position), line, font=system_font, fill=0)
            y_position += 20  # Increment y for the next line (adjust spacing as needed)

        rotated_canvas2 = canvas2.rotate(90, expand=True)
        print("Refreshing Screen (Blinking will take ~20 seconds)...")
        epd.display(epd.getbuffer(rotated_canvas2))
        # Draw new text
        
        #draw2.text((30, 60), "Keep Winning!" , font=system_font, fill=0)

        #img = Image.open('bild.png')
        #img_processed = img.resize((epd.width, epd.height)).convert('1')
        #epd.display(epd.getbuffer(img_processed))
        # Rotate the canvas 90 degrees
        #rotated_canvas2 = canvas2.rotate(90, expand=True)

        #print("Refreshing Screen Again...")
        #epd.display(epd.getbuffer(rotated_canvas2))
        
        # ==========================================
        # STEP 4: SAFE DISCONNECT
        # ==========================================
        print("Finalizing updates. Putting display to sleep...")
        epd.sleep()
        print("Finished successfully!")


@app.route('/print', methods=['POST'])
def print_message():
    """
    Handle the form submission.
    Prints the message to CLI and displays it on the e-paper.
    """
    # Get the message from the form
    message = request.form.get('message', 'Hello World')
    
    # Print to CLI
    print(f"Printed: {message}")
    
    # Display on e-paper
    display_on_epaper(message)
    
    # Render the template with success message
    return render_template('index.html', printed_message=message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
