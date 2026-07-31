import sys
import os
import time
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request

app = Flask(__name__)

# Try to import the waveshare e-paper library
# Try multiple possible import paths
EPD_AVAILABLE = False
EPD_MODULE = None
try:
    from lib.waveshare_epd import epd2in15g
    EPD_MODULE = epd2in15g
    EPD_AVAILABLE = True
except ImportError:
    try:
        from waveshare_epd import epd2in15g
        EPD_MODULE = epd2in15g
        EPD_AVAILABLE = True
    except ImportError:
        try:
            sys.path.append('/usr/local/lib/python3/dist-packages')
            from lib.waveshare_epd import epd2in15g
            EPD_MODULE = epd2in15g
            EPD_AVAILABLE = True
        except ImportError:
            print("Warning: Waveshare e-paper library not available. Display functionality disabled.")
            print("Please install: pip install waveshare-epd or ensure lib/waveshare_epd is in your PYTHONPATH")

# Try to import gpiozero for cleanup
try:
    import gpiozero
    GPIOZERO_AVAILABLE = True
except ImportError:
    GPIOZERO_AVAILABLE = False
    print("Warning: gpiozero not available, GPIO cleanup disabled")


@app.route('/')
def index():
    """Render the main page with the form."""
    return render_template('index.html', printed_message=None)


def cleanup_gpio():
    """Clean up any stuck GPIO pins before initializing the display."""
    if GPIOZERO_AVAILABLE:
        try:
            # Shutdown all GPIO devices
            gpiozero.Device.shutdown_all()
            print("Cleaned up GPIO devices")
            time.sleep(0.5)  # Give time for cleanup
        except Exception as e:
            print(f"Warning: Could not clean up GPIO: {e}")


def display_on_epaper(message):
    """
    Display a message on the Waveshare e-paper display.
    Uses the same approach as quick_test.py: creates canvas with reversed dimensions
    (height x width) for portrait design, then rotates 90 degrees for landscape display.
    """
    if not EPD_AVAILABLE:
        print("E-paper display not available - library not imported")
        return False
    
    try:
        print(f"Attempting to display: '{message}'")
        
        # Clean up GPIO before initializing
        cleanup_gpio()
        
        # Initialize the e-paper display
        epd = EPD_MODULE.EPD()
        print("EPD object created")
        
        epd.init()
        print("EPD initialized")
        
        epd.Clear()
        print("EPD cleared")
        
        # Load system font with safety fallback
        try:
            system_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20)
        except OSError:
            system_font = ImageFont.load_default()
            print("Using default font")
        
        # Create canvas with REVERSED dimensions (Height x Width) for portrait design
        # This matches the approach in quick_test.py
        print(f"Creating canvas for e-paper (height: {epd.height}, width: {epd.width})")
        canvas = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(canvas)
        
        # Draw the message on the portrait canvas
        draw.text((10, 30), message, font=system_font, fill=0)
        print("Text drawn on canvas")
        
        # Rotate the canvas 90 degrees to fit the landscape hardware screen
        rotated_canvas = canvas.rotate(90, expand=True)
        print("Canvas rotated")
        
        # Display the rotated image
        print("Displaying message on e-paper (this may take ~20 seconds)...")
        epd.display(epd.getbuffer(rotated_canvas))
        print("Message displayed successfully on e-paper!")
        
        # Put the display to sleep to save power
        epd.sleep()
        print("EPD put to sleep")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error displaying on e-paper: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return False


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
