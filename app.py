from flask import Flask, render_template, request

app = Flask(__name__)

# Store the last printed message for display
last_printed_message = None


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
    """
    Handle the form submission.
    Prints the message to CLI and displays confirmation in the UI.
    """
    global last_printed_message
    
    # Get the message from the form
    message = request.form.get('message', 'Hello World')
    
    # Print to CLI
    print(f"Printed: {message}")
    
    # Store the last printed message
    last_printed_message = message
    
    # Render the template with success message
    return render_template(
        'index.html',
        printed_message=message,
        last_printed=last_printed_message
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
