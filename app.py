import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template('index.html', printed_message=None)


def display_on_epaper(message):
    """
    Display a message on the Waveshare e-paper display.
    Supports multi-line text with automatic line wrapping.
    Uses the same approach as quick_test.py: creates canvas with reversed dimensions
    (height x width) for portrait design, then rotates 90 degrees for landscape display.
    """
    from lib.waveshare_epd import epd2in15g 

    try:
        epd = epd2in15g.EPD()
        epd.init()
        print("EPD initialized")
        
        epd.Clear()

        # Load system font with safety fallback
        try:
            system_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except OSError:
            system_font = ImageFont.load_default()
            print("Using default font")
        
        # Split message into lines (supports both newline-separated and comma-separated)
        lines = message.replace(',', '\n').split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # If no lines or empty, use default
        if not lines:
            lines = ["Hello World"]
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Draw each line on the portrait canvas
        y_position = 30
        line_height = 25  # Space between lines
        
        for line in lines:
            draw.text((10, y_position), line, font=system_font, fill=0)
            y_position += line_height
            # Stop if we're running out of vertical space
            if y_position > epd.width - 30:
                print(f"Warning: Not enough space for all lines. Displaying first {lines.index(line) + 1} lines.")
                break
        
        # Rotate the canvas 90 degrees to fit the landscape hardware screen
        rotated_canvas = canvas.rotate(90, expand=True)
        print("Refreshing Screen (Blinking will take ~20 seconds)...")
        epd.display(epd.getbuffer(rotated_canvas))
        print("Frame displayed.")

        print("Finalizing updates. Putting display to sleep...")
        epd.sleep()
        print("Finished successfully!")

    except Exception as e:
        print(f"Error encountered: {e}")


@app.route('/print', methods=['POST'])
def print_message():
    """
    Handle the form submission.
    Prints the message to CLI and displays it on the e-paper.
    """
    # Get the message from the form
    message = request.form.get('message', 'Hello World')
    
    print(f"Printed: {message}")
    display_on_epaper(message)
    
    # Render the template with success message
    return render_template('index.html', printed_message=message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
