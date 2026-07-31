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

# Calculate max characters per line based on display width (200px after rotation)
# Approximate character widths at different font sizes
CHAR_WIDTHS = {
    'small': 8,    # ~8px per char at 12px font
    'medium': 11,  # ~11px per char at 18px font
    'large': 15,   # ~15px per char at 24px font
    'xlarge': 18   # ~18px per char at 30px font
}

# Display dimensions after rotation (200x200)
DISPLAY_WIDTH = 200
DISPLAY_HEIGHT = 200


def get_max_chars_per_line(font_size_key):
    """Calculate maximum characters that fit in one line."""
    char_width = CHAR_WIDTHS.get(font_size_key, 12)
    # Leave some margin (20px total: 10px left + 10px right)
    return max(1, (DISPLAY_WIDTH - 20) // char_width)


def get_max_lines(font_size_key):
    """Calculate maximum lines that fit on the display."""
    font_size = FONT_SIZES.get(font_size_key, 20)
    line_height = font_size + 8  # padding
    # Leave some margin (40px total: 20px top + 20px bottom)
    return max(1, (DISPLAY_HEIGHT - 40) // line_height)


def get_max_total_chars(font_size_key):
    """Calculate maximum total characters (chars per line * max lines)."""
    return get_max_chars_per_line(font_size_key) * get_max_lines(font_size_key)


@app.route('/')
def index():
    """Render the main page with the form."""
    default_font = 'medium'
    return render_template('index.html', 
                         printed_message=None,
                         font_sizes=FONT_SIZES,
                         default_font=default_font,
                         max_chars_per_line={k: get_max_chars_per_line(k) for k in FONT_SIZES},
                         max_lines={k: get_max_lines(k) for k in FONT_SIZES},
                         max_total_chars={k: get_max_total_chars(k) for k in FONT_SIZES})


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
    Supports multi-line text with adjustable font size and automatic truncation.
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
        
        # Calculate limits
        max_chars_per_line = get_max_chars_per_line(font_size_key)
        max_lines = get_max_lines(font_size_key)
        
        # Split message into lines (supports both newline-separated and comma-separated)
        lines = message.replace(',', '\n').split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # If no lines or empty, use default
        if not lines:
            lines = ["Hello World"]
        
        # Truncate lines that are too long
        truncated_lines = []
        for line in lines[:max_lines]:  # Limit to max lines
            if len(line) > max_chars_per_line:
                truncated_lines.append(line[:max_chars_per_line] + '...')
            else:
                truncated_lines.append(line)
        
        print(f"Displaying {len(truncated_lines)} lines (max {max_lines})")
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Calculate line height based on font size
        line_height = font_size + 8  # Add some padding between lines
        
        # Draw each line on the portrait canvas
        y_position = 20  # Start a bit higher for larger fonts
        
        for line in truncated_lines:
            draw.text((10, y_position), line, font=system_font, fill=0)
            y_position += line_height
        
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
                         default_font=font_size,
                         max_chars_per_line={k: get_max_chars_per_line(k) for k in FONT_SIZES},
                         max_lines={k: get_max_lines(k) for k in FONT_SIZES},
                         max_total_chars={k: get_max_total_chars(k) for k in FONT_SIZES})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
