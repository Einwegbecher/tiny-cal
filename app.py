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

# Actual display resolution (296x160) - this is the CORRECT resolution
DISPLAY_WIDTH = 296
DISPLAY_HEIGHT = 160


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


def get_text_width(text, font):
    """Calculate the actual pixel width of text using the given font."""
    # Create a temporary image to measure text
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    # Use textbbox to get the bounding box (left, top, right, bottom)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]  # right - left = width


def get_text_height(font):
    """Calculate the actual pixel height of text using the given font."""
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), "Ag", font=font)  # Use 'Ag' to get ascender + descender
    return bbox[3] - bbox[1]  # bottom - top = height


def wrap_text_dynamically(text, font, max_width):
    """
    Wrap text to multiple lines based on actual pixel measurements.
    Preserves existing newlines and wraps long lines at word boundaries.
    """
    lines = []
    current_line = ""
    
    # Split by existing newlines first
    for paragraph in text.split('\n'):
        paragraph = paragraph.strip()
        if not paragraph:
            if current_line:
                lines.append(current_line)
                current_line = ""
            continue
            
        # Process each word
        for word in paragraph.split():
            # Check if adding this word would exceed max_width
            test_line = current_line + (' ' + word if current_line else word)
            test_width = get_text_width(test_line, font)
            
            if test_width <= max_width:
                current_line = test_line
            else:
                # Word doesn't fit, start new line
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        # Don't forget the last line of the paragraph
        if current_line:
            lines.append(current_line)
            current_line = ""
    
    # Add any remaining text
    if current_line:
        lines.append(current_line)
    
    return lines


@app.route('/')
def index():
    """Render the main page with the form."""
    default_font = 'medium'
    # Get last message from session if available
    last_message = session.get('last_message', '')
    return render_template('index.html', 
                         printed_message=None,
                         font_sizes=FONT_SIZES,
                         default_font=default_font,
                         last_message=last_message)


def display_on_epaper(message, font_size_key='medium'):
    """
    Display a message on the Waveshare e-paper display.
    Uses dynamic pixel-based line wrapping for perfect fit.
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
        
        # Get actual text measurements
        text_height = get_text_height(system_font)
        line_spacing = 2  # Small spacing between lines
        total_line_height = text_height + line_spacing
        
        # Calculate available space (account for margins)
        margin_left = 10
        margin_right = 10
        margin_top = 10
        margin_bottom = 10
        
        available_width = DISPLAY_WIDTH - margin_left - margin_right
        available_height = DISPLAY_HEIGHT - margin_top - margin_bottom
        
        # Calculate max lines
        max_lines = max(1, available_height // total_line_height)
        
        print(f"Available width: {available_width}px, height: {available_height}px")
        print(f"Text height: {text_height}px, line height: {total_line_height}px")
        print(f"Max lines: {max_lines}")
        
        # Wrap text based on actual pixel width
        raw_text = message.replace(',', '\n')
        wrapped_lines = wrap_text_dynamically(raw_text, system_font, available_width)
        
        # If no lines, use default
        if not wrapped_lines:
            wrapped_lines = ["Hello World"]
        
        # Limit to max lines that fit on display
        display_lines = wrapped_lines[:max_lines]
        
        print(f"Displaying {len(display_lines)} lines (max {max_lines})")
        for i, line in enumerate(display_lines):
            width = get_text_width(line, system_font)
            print(f"  Line {i+1} ({width}px): {line}")
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Draw each line on the portrait canvas
        y_position = margin_top
        
        for line in display_lines:
            draw.text((margin_left, y_position), line, font=system_font, fill=0)
            y_position += total_line_height
        
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
        import traceback
        traceback.print_exc()
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
                         last_message=message)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
