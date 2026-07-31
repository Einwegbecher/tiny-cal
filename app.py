import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, session

app = Flask(__name__)
app.secret_key = 'e-paper-display-secret-key-12345'

# Available font sizes for the e-paper display (only Medium and XLarge)
FONT_SIZES = {
    'medium': 18,
    'xlarge': 30
}

# Character width estimates for each font size
CHAR_WIDTHS = {
    'medium': 10,   # ~10px per char at 18px font
    'xlarge': 18    # ~18px per char at 30px font
}

# Display dimensions after rotation (200x200)
DISPLAY_WIDTH = 200
DISPLAY_HEIGHT = 200


def get_font(size_key, fallback_size=18):
    """Get the font object for the specified size."""
    size = FONT_SIZES.get(size_key, fallback_size)
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
    except OSError:
        try:
            return ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf', size)
        except OSError:
            return ImageFont.load_default()


def get_max_chars_per_line(font_size_key):
    """Calculate maximum characters that fit in one line."""
    char_width = CHAR_WIDTHS.get(font_size_key, 10)
    # Leave margin: 10px left + 10px right = 20px total
    return max(1, (DISPLAY_WIDTH - 20) // char_width)


def get_max_lines(font_size_key):
    """Calculate maximum lines that fit on the display."""
    font_size = FONT_SIZES.get(font_size_key, 18)
    line_height = font_size + 2  # Reduced padding for tighter spacing
    # Leave margin: 15px top + 15px bottom = 30px total
    return max(1, (DISPLAY_HEIGHT - 30) // line_height)


def wrap_text(text, max_chars_per_line):
    """
    Wrap text to multiple lines if it exceeds max_chars_per_line.
    Preserves existing newlines and wraps long lines at word boundaries.
    """
    lines = []
    # Split by existing newlines first
    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # Split long lines into chunks
        while len(paragraph) > max_chars_per_line:
            # Find the last space before max_chars_per_line to avoid breaking words
            split_pos = paragraph[:max_chars_per_line].rfind(' ')
            if split_pos <= 0:  # No space found, force break
                split_pos = max_chars_per_line
            lines.append(paragraph[:split_pos])
            paragraph = paragraph[split_pos:].lstrip()
        if paragraph:
            lines.append(paragraph)
    return lines


@app.route('/')
def index():
    """Render the main page with the form."""
    default_font = 'medium'
    # Get last message from session if available
    last_message = session.get('last_message', 'Hello World\nThis is a test of the e-paper display with automatic line wrapping.')
    return render_template('index.html', 
                         printed_message=None,
                         font_sizes=FONT_SIZES,
                         default_font=default_font,
                         last_message=last_message,
                         max_chars_per_line={k: get_max_chars_per_line(k) for k in FONT_SIZES},
                         max_lines={k: get_max_lines(k) for k in FONT_SIZES})


def display_on_epaper(message, font_size_key='medium'):
    """
    Display a message on the Waveshare e-paper display.
    Supports multi-line text with automatic line wrapping and font size control.
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
        system_font = get_font(font_size_key, 18)
        font_size = FONT_SIZES.get(font_size_key, 18)
        print(f"Using font size: {font_size}px")
        
        # Calculate limits
        max_chars_per_line = get_max_chars_per_line(font_size_key)
        max_lines = get_max_lines(font_size_key)
        
        # Split message into lines (supports both newline-separated and comma-separated)
        raw_lines = message.replace(',', '\n').split('\n')
        
        # Wrap each line to fit display width
        wrapped_lines = []
        for line in raw_lines:
            line = line.strip()
            if line:
                wrapped_lines.extend(wrap_text(line, max_chars_per_line))
        
        # If no lines, use default
        if not wrapped_lines:
            wrapped_lines = ["Hello World"]
        
        # Limit to max lines that fit on display - STOP here, no disappearing text
        display_lines = wrapped_lines[:max_lines]
        
        print(f"Displaying {len(display_lines)} lines (max {max_lines})")
        for i, line in enumerate(display_lines):
            print(f"  Line {i+1}: {line}")
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Calculate line height based on font size - tighter spacing
        line_height = font_size + 2  # Reduced from 8 to 2 for tighter spacing
        
        # Draw each line on the portrait canvas - less top margin
        y_position = 10  # Reduced from 20 to 10
        
        for line in display_lines:
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
        return True

    except Exception as e:
        print(f"Error encountered: {e}")
        return False


@app.route('/print', methods=['POST'])
def print_message():
    """
    Handle the form submission.
    Prints the message to CLI and displays it on the e-paper.
    """
    # Get the message and font size from the form
    message = request.form.get('message', 'Hello World')
    font_size = request.form.get('font_size', 'medium')
    
    # Store the message in session for next page load
    session['last_message'] = message
    
    print(f"Printing: {message}")
    print(f"Font size: {font_size}")
    
    # Show printing message
    success_message = "Printing..."
    
    # Display on e-paper (this takes ~20 seconds)
    display_success = display_on_epaper(message, font_size)
    
    # Update message based on success
    if display_success:
        success_message = "Printed!"
    else:
        success_message = "Printing failed"
    
    # Render the template with success message
    return render_template('index.html', 
                         printed_message=success_message,
                         font_sizes=FONT_SIZES,
                         default_font=font_size,
                         last_message=message,
                         max_chars_per_line={k: get_max_chars_per_line(k) for k in FONT_SIZES},
                         max_lines={k: get_max_lines(k) for k in FONT_SIZES})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
