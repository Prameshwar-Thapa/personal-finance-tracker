import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_receipt_file(file, user_id):
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{user_id}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create user-specific directory
        user_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id))
        os.makedirs(user_upload_dir, exist_ok=True)
        
        file_path = os.path.join(user_upload_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # If it's an image, create a thumbnail
        if ext.lower() in ['.png', '.jpg', '.jpeg']:
            try:
                create_thumbnail(file_path, user_id, unique_filename)
            except Exception as e:
                print(f"Error creating thumbnail: {e}")
        
        return unique_filename
    
    return None

def create_thumbnail(file_path, user_id, filename):
    """Create a thumbnail for uploaded images"""
    try:
        with Image.open(file_path) as img:
            img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save thumbnail
            name, ext = os.path.splitext(filename)
            thumb_filename = f"{name}_thumb{ext}"
            thumb_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(user_id), 'thumbnails')
            os.makedirs(thumb_dir, exist_ok=True)
            
            thumb_path = os.path.join(thumb_dir, thumb_filename)
            img.save(thumb_path, optimize=True, quality=85)
            
    except Exception as e:
        print(f"Error creating thumbnail: {e}")

def format_currency(amount):
    """Format amount as currency"""
    return f"${amount:,.2f}"

def calculate_monthly_budget_usage(user_id, category_id, month, year):
    """Calculate budget usage for a category in a specific month"""
    # This would be implemented when budget features are added
    pass
