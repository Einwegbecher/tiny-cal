import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request

app = Flask(__name__)

# Available font sizes for the e-paper display
FONT_SIZES = {
    'small': 12,
    'medium': 18,
    'large': 24,
    'xlarge': 30
}


@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template('index.html', 
                         printed_message=None,
                         font_sizes=FONT_SIZES,
                         default_font='medium')


def get_font(size_key, fallback_size=20):
    """Get the font object for the specified size."""
    size = FONT_SIZES.get(size_key, fallback_size)
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except OSError:
        try:
            return ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', size)
        except OSError:
            return ImageFont.load_default()


def display_on_epaper(message, font_size_key='medium'):
    """
    Display a message on the Waveshare e-paper display.
    Supports multi-line text with adjustable font size.
    Uses the same approach as quick_test.py: creates canvas with reversed dimensions
    (height x width) for portrait design, then rotates 90 degrees for landscape display.
    """
    from lib.waveshare_epd import epd2in15g 

    try:
        epd = epd2in15g.EPD()
        epd.init()
        print("EPD initialized")
        
        epd.Clear()

        # Get font based on selected size
        system_font = get_font(font_size_key, 20)
        font_size = FONT_SIZES.get(font_size_key, 20)
        print(f"Using font size: {font_size}px")
        
        # Split message into lines (supports both newline-separated and comma-separated)
        lines = message.replace(',', '\n').split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # If no lines or empty, use default
        if not lines:
            lines = ["Hello World"]
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Calculate line height based on font size
        line_height = font_size + 8  # Add some padding between lines
        
        # Draw each line on the portrait canvas
        y_position = 20  # Start a bit higher for larger fonts
        
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
    # Get the message and font size from the form
    message = request.form.get('message', 'Hello World')
    font_size = request.form.get('font_size', 'medium')
    
    print(f"Printed: {message}")
    print(f"Font size: {font_size}")
    display_on_epaper(message, font_size)
    
    # Render the template with success message
    return render_template('index.html', 
                         printed_message=message,
                         font_sizes=FONT_SIZES,
                         default_font=font_size)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
