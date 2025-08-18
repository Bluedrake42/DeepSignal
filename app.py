from flask import Flask, request, render_template, jsonify, url_for
from flask_mail import Mail, Message
from pymongo import MongoClient
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from datetime import datetime, timedelta
import os
import re
import logging
import configparser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load site configuration
def load_site_config():
    """Load site configuration from settings.cfg"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'settings.cfg')
    
    # Default configuration
    default_config = {
        'site': {
            'title': 'Deep Signal',
            'subtitle': 'Direct Creator Connections'
        },
        'content_categories': {
            'categories': 'Game Development\nArtificial Intelligence\nTactical Video Games\nPersonal Updates'
        }
    }
    
    try:
        config.read(config_path)
        
        # Get site settings
        site_title = config.get('site', 'title', fallback=default_config['site']['title'])
        site_subtitle = config.get('site', 'subtitle', fallback=default_config['site']['subtitle'])
        
        # Get categories - split by newlines and clean up
        categories_raw = config.get('content_categories', 'categories', 
                                  fallback=default_config['content_categories']['categories'])
        categories = [cat.strip() for cat in categories_raw.split('\n') if cat.strip()]
        
        # Get email message settings
        validation_subject = config.get('email_messages', 'validation_subject', 
                                      fallback='Please validate your email')
        validation_message = config.get('email_messages', 'validation_message', 
                                       fallback='Thank you for joining our community. Please click the link below to confirm your email:')
        welcome_subject = config.get('email_messages', 'welcome_subject', 
                                   fallback='Welcome - You\'re connected!')
        welcome_message = config.get('email_messages', 'welcome_message', 
                                    fallback='Thank you for confirming your email. You\'re now part of our community.')
        sender_name = config.get('email_messages', 'sender_name', 
                               fallback='The Team')
        
        return {
            'title': site_title,
            'subtitle': site_subtitle,
            'categories': categories,
            'validation_subject': validation_subject,
            'validation_message': validation_message,
            'welcome_subject': welcome_subject,
            'welcome_message': welcome_message,
            'sender_name': sender_name
        }
        
    except Exception as e:
        logger.warning(f"Error loading settings.cfg: {e}. Using default configuration.")
        # Return default configuration if file can't be read
        categories = [cat.strip() for cat in default_config['content_categories']['categories'].split('\n') if cat.strip()]
        return {
            'title': default_config['site']['title'],
            'subtitle': default_config['site']['subtitle'],
            'categories': categories,
            'validation_subject': 'Please validate your email',
            'validation_message': 'Thank you for joining our community. Please click the link below to confirm your email:',
            'welcome_subject': 'Welcome - You\'re connected!',
            'welcome_message': 'Thank you for confirming your email. You\'re now part of our community.',
            'sender_name': 'The Team'
        }

# Load site configuration
site_config = load_site_config()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Email Configuration (AWS SES)
app.config.update(
    MAIL_SERVER=os.getenv('MAIL_SERVER', 'email-smtp.us-east-2.amazonaws.com'),
    MAIL_PORT=int(os.getenv('MAIL_PORT', '587')),
    MAIL_USE_TLS=os.getenv('MAIL_USE_TLS', 'True').lower() == 'true',
    MAIL_USE_SSL=os.getenv('MAIL_USE_SSL', 'False').lower() == 'true',
    MAIL_USERNAME=os.getenv('SES_SMTP_USERNAME'),
    MAIL_PASSWORD=os.getenv('SES_SMTP_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.getenv('MAIL_DEFAULT_SENDER', 'noreply@yourdomain.com')
)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize token serializer for email validation
serializer = URLSafeTimedSerializer(app.secret_key)

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'deepsignal')

# MongoDB client with lazy initialization
_mongo_client = None

def get_mongo_client():
    """Get MongoDB client with lazy initialization"""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGO_URI)
            # Test the connection
            _mongo_client.admin.command('ping')
            logger.info("MongoDB connection successful")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise e
    return _mongo_client

def get_db():
    """Get database connection"""
    client = get_mongo_client()
    return client[DATABASE_NAME]

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_validation_token(email):
    """Generate email validation token"""
    return serializer.dumps(email, salt='email-validation')

def verify_validation_token(token, max_age=3600):
    """Verify email validation token (default 1 hour expiry)"""
    try:
        email = serializer.loads(token, salt='email-validation', max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None

def send_validation_email(email, validation_token):
    """Send email validation email"""
    try:
        validation_url = url_for('validate_email', token=validation_token, _external=True)
        
        subject = site_config['validation_subject']
        body = f"""
{site_config['validation_message']}
{validation_url}

This link will expire in 1 hour for security purposes.

If you didn't request this, please ignore this email.

Best regards,
{site_config['sender_name']}
"""
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logger.info(f"Validation email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send validation email to {email}: {e}")
        return False

def send_welcome_email(email, preferences):
    """Send welcome email after validation"""
    try:
        subject = site_config['welcome_subject']
        
        preferences_text = ""
        if preferences:
            preferences_text = f"\n\nYour selected content interests:\n" + "\n".join([f"• {pref}" for pref in preferences])
        
        body = f"""
{site_config['welcome_message']}{preferences_text}

Best regards,
{site_config['sender_name']}
"""
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        mail.send(msg)
        logger.info(f"Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {email}: {e}")
        return False

@app.route('/')
def index():
    """Serve the main Deep Signal audience signup page"""
    return render_template('index.html', config=site_config)

@app.route('/submit_email', methods=['POST'])
def submit_email():
    """Handle email submission for Deep Signal audience signup"""
    try:
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email address is required'}), 400
        
        if not is_valid_email(email):
            return jsonify({'success': False, 'message': 'Please enter a valid email address'}), 400
        
        db = get_db()
        subscribers = db.subscribers
        
        # Check if email already exists
        existing_subscriber = subscribers.find_one({'email': email})
        
        if existing_subscriber:
            if existing_subscriber.get('email_validated', False):
                return jsonify({'success': False, 'message': 'This email is already subscribed and validated'}), 400
            else:
                # Resend validation email for unvalidated subscriber
                validation_token = generate_validation_token(email)
                if send_validation_email(email, validation_token):
                    # Update the validation token in database
                    subscribers.update_one(
                        {'email': email},
                        {
                            '$set': {
                                'validation_token': validation_token,
                                'token_created_at': datetime.utcnow(),
                                'updated_at': datetime.utcnow()
                            }
                        }
                    )
                    return jsonify({'success': True, 'message': 'A new validation email has been sent to your inbox'}), 200
                else:
                    return jsonify({'success': False, 'message': 'Failed to send validation email. Please try again.'}), 500
        
        # Create new subscriber record
        validation_token = generate_validation_token(email)
        
        subscriber_data = {
            'email': email,
            'email_validated': False,
            'validation_token': validation_token,
            'token_created_at': datetime.utcnow(),
            'content_preferences': [],
            'signup_date': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'validation_date': None
        }
        
        # Insert subscriber
        result = subscribers.insert_one(subscriber_data)
        
        # Send validation email
        if send_validation_email(email, validation_token):
                            return jsonify({'success': True, 'message': 'Please check your email and click the validation link to complete your subscription'}), 200
        else:
            # Remove the subscriber if email sending failed
            subscribers.delete_one({'_id': result.inserted_id})
            return jsonify({'success': False, 'message': 'Failed to send validation email. Please try again.'}), 500
        
    except Exception as e:
        logger.error(f"Error in submit_email: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

@app.route('/submit_survey', methods=['POST'])
def submit_survey():
    """Handle content preferences submission"""
    try:
        email = request.form.get('email', '').strip().lower()
        preferences = request.form.getlist('preferences')
        
        if not email:
            return jsonify({'success': False, 'message': 'Email address is required'}), 400
        
        db = get_db()
        subscribers = db.subscribers
        
        # Update preferences for the subscriber
        result = subscribers.update_one(
            {'email': email},
            {
                '$set': {
                    'content_preferences': preferences,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        if result.modified_count > 0:
            return jsonify({'success': True, 'message': 'Preferences updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Subscriber not found'}), 404
        
    except Exception as e:
        logger.error(f"Error in submit_survey: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500

@app.route('/validate/<token>')
def validate_email(token):
    """Handle email validation from validation link"""
    try:
        email = verify_validation_token(token)
        
        if not email:
            return render_template('validation_result.html', 
                                 success=False, 
                                 message="Invalid or expired validation link. Please try subscribing again.")
        
        db = get_db()
        subscribers = db.subscribers
        
        # Find and update the subscriber
        subscriber = subscribers.find_one({'email': email})
        
        if not subscriber:
            return render_template('validation_result.html', 
                                 success=False, 
                                 message="Subscriber not found. Please try subscribing again.")
        
        if subscriber.get('email_validated', False):
            return render_template('validation_result.html', 
                                 success=True, 
                                 message="Your email is already validated. Welcome!")
        
        # Update subscriber as validated
        subscribers.update_one(
            {'email': email},
            {
                '$set': {
                    'email_validated': True,
                    'validation_date': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                },
                '$unset': {
                    'validation_token': "",
                    'token_created_at': ""
                }
            }
        )
        
        # Send welcome email
        preferences = subscriber.get('content_preferences', [])
        send_welcome_email(email, preferences)
        
        return render_template('validation_result.html', 
                             success=True, 
                             message="Welcome! Your email has been validated and you're now subscribed.")
        
    except Exception as e:
        logger.error(f"Error in validate_email: {e}")
        return render_template('validation_result.html', 
                             success=False, 
                             message="An error occurred during validation. Please try again.")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = get_db()
        db.command('ping')
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)