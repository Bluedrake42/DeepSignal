# Deep Signal

A platform for content creators to build direct audience connections outside traditional platforms. Founded by Bluedrake42, Deep Signal enables creators to reach their community with categorized content delivery based on individual interests, ensuring uninterrupted access to your audience.

## 🌟 Features

- **Direct Audience Building**: Connect with your community without platform interference
- **Categorized Content Delivery**: Target specific audience segments based on their interests
- **Email Validation**: Secure token-based verification system with 1-hour expiry
- **Interest-Based Preferences**: Audience members select content categories they want to receive
- **AWS SES Integration**: Professional email delivery with proper DNS setup
- **MongoDB Storage**: Robust data storage with comprehensive audience tracking
- **Modern UI**: Beautiful particle background with responsive design
- **Creator-Focused**: Built specifically for content creators seeking platform independence

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file with your credentials:

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_DEBUG=True
PORT=5000

# AWS SES Configuration
MAIL_SERVER=email-smtp.us-east-2.amazonaws.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
SES_SMTP_USERNAME=your-ses-smtp-username
SES_SMTP_PASSWORD=your-ses-smtp-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DATABASE_NAME=deepsignal

# Optional: For production deployments
# MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
# MAIL_SERVER=email-smtp.us-west-2.amazonaws.com  # Choose your region
```

### 3. Start the Application

```bash
python app.py
```

Visit `http://localhost:5000` to see your Deep Signal audience signup form!

## ⚙️ Detailed Setup Instructions

### AWS SES Setup

1. **Create AWS Account & Access SES**
   - Sign up for AWS at https://aws.amazon.com/
   - Navigate to Simple Email Service (SES)
   - Choose your region (e.g., us-east-2)

2. **Verify Your Domain/Email**
   - In SES Console → Verified Identities
   - Click "Create Identity"
   - Choose "Domain" or "Email address"
   - Follow verification instructions

3. **Request Production Access**
   - By default, SES is in "Sandbox mode"
   - Request production access to send to any email
   - SES Console → Account dashboard → Request production access

4. **Create SMTP Credentials**
   - SES Console → SMTP settings
   - Click "Create SMTP credentials"
   - Create IAM user with SMTP access
   - Save the username/password for your `.env` file

5. **Set Up DNS Records (for domain verification)**
   ```dns
   # SPF Record
   TXT: v=spf1 include:amazonses.com ~all

   # DKIM Records (provided by AWS)
   # Add the CNAME records AWS provides for DKIM

   # DMARC (optional but recommended)
   TXT: v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
   ```

### MongoDB Setup

#### Option 1: Local MongoDB
1. **Install MongoDB**
   - Download from https://www.mongodb.com/try/download/community
   - Follow installation instructions for your OS
   - Start MongoDB service

2. **Use Default Configuration**
   ```bash
   MONGO_URI=mongodb://localhost:27017/
   ```

#### Option 2: MongoDB Atlas (Cloud)
1. **Create Atlas Account**
   - Sign up at https://www.mongodb.com/atlas
   - Create a free tier cluster

2. **Get Connection String**
   - Cluster → Connect → Connect your application
   - Copy the connection string
   - Replace `<password>` with your database user password

3. **Update Environment**
   ```bash
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

## 📊 Database Schema

The application automatically creates these collections:

### `subscribers` Collection
```javascript
{
  "_id": ObjectId,
  "email": "user@example.com",
  "email_validated": true,
  "validation_token": "token-string", // Only present if not validated
  "token_created_at": ISODate,       // Only present if not validated
  "content_preferences": ["Gaming", "Tech Reviews", "Live Streams"],
  "signup_date": ISODate,
  "validation_date": ISODate,        // Only after validation
  "updated_at": ISODate
}
```

## 🔐 Security Considerations

### Environment Variables
- **Never commit `.env` to version control**
- Use strong, unique values for `SECRET_KEY`
- Rotate SMTP credentials regularly

### Email Security
- Enable DKIM authentication
- Set up SPF and DMARC records
- Monitor bounce and complaint rates

### Database Security
- Use MongoDB authentication in production
- Enable SSL/TLS for connections
- Regular backups and monitoring

## 📧 Audience Connection Flow

1. **Audience Member Joins**
   - Form validation on frontend
   - Email stored in MongoDB as unvalidated
   - Validation email sent via SES

2. **Email Validation**
   - User clicks validation link
   - Token verified and user marked as validated
   - Welcome email sent
   - Content preferences applied

3. **Creator Dashboard Updates**
   - All interactions logged with timestamps
   - Audience preferences can be updated
   - Connection status tracked

## 🛠️ API Endpoints

- `GET /` - Deep Signal audience signup page
- `POST /submit_email` - Audience member subscription
- `POST /submit_survey` - Update content preferences
- `GET /validate/<token>` - Email validation
- `GET /health` - System health check

## 🚨 Troubleshooting

### Common Issues

1. **Email Not Sending**
   - Check SES credentials in `.env`
   - Verify sender email is validated in SES
   - Check if still in SES sandbox mode

2. **Database Connection Failed**
   - Verify MongoDB is running (local)
   - Check connection string format
   - Ensure network access (Atlas)

3. **Validation Links Not Working**
   - Check `SECRET_KEY` is set
   - Verify token hasn't expired (1 hour)
   - Check Flask app is accessible externally

### Health Check
Visit `/health` to verify:
- Database connectivity
- Application status

### Logs
Check application logs for detailed error information:
```bash
# Development
python app.py

# Production
gunicorn -w 4 -b 0.0.0.0:5000 app:app --log-level info
```

## 🚀 Production Deployment

### Environment Updates
```bash
# Production settings
SECRET_KEY=your-production-secret-key
FLASK_DEBUG=False
PORT=5000

# Use production MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/deepsignal

# Use appropriate SES region
MAIL_SERVER=email-smtp.us-east-2.amazonaws.com
```

### Deployment Options
- **Heroku**: Add MongoDB Atlas and SES credentials
- **DigitalOcean**: Use App Platform or Droplets
- **AWS**: EC2 with RDS or native services
- **Docker**: Create Dockerfile for containerization

## 📁 Project Structure

```
DeepSignal/
├── app.py                          # Main Flask application
├── settings.cfg                    # Site configuration (title, categories)
├── requirements.txt                # Python dependencies
├── templates/
│   ├── index.html                 # Deep Signal audience signup page
│   └── validation_result.html     # Email validation result
├── .env                           # Environment variables (create from example)
└── README.md                      # This file
```

## 🎨 UI Features

- **Particle Background**: Dynamic animated particle system
- **Responsive Design**: Works on all screen sizes
- **Loading States**: Visual feedback during form submission
- **Error Handling**: Clear user-friendly error messages
- **Content Preferences**: Optional category selection
- **Modern Styling**: Glass morphism effects with red theme

## ⚙️ Site Customization

Deep Signal can be easily customized using the `settings.cfg` file:

### Site Configuration

Edit `settings.cfg` to customize your instance:

```ini
[site]
title = Your Brand Name
subtitle = Your Custom Tagline
button_text = Subscribe Now

[content_categories]
categories = Category 1
    Category 2
    Category 3
    Custom Category
```

### Configuration Options

- **title**: Main heading displayed on signup page
- **subtitle**: Tagline below the main title
- **button_text**: Text displayed on the signup button
- **categories**: Content categories for user preferences (one per line)

### Examples

**Gaming Creator:**
```ini
[site]
title = GameMaster Studios
subtitle = Premium Gaming Content
button_text = Join the Guild

[content_categories]
categories = Game Reviews
    Live Streams
    Beta Access
    Community Events
```

**Tech Creator:**
```ini
[site]
title = TechVision
subtitle = Cutting-Edge Technology Insights
button_text = Get Tech Updates

[content_categories]
categories = Product Reviews
    Tutorials
    Industry News
    Hardware Guides
```

The application automatically reloads configuration changes - no restart required!

Build your independent creator community with Deep Signal! 🎉
