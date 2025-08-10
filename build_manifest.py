#!/usr/bin/env python3
"""
Build script: Handle environment variable replacement
Replace placeholders in manifest.json with actual values
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

def build_manifest():
    """Build manifest.json, replace environment variables"""
    
    # Load environment variables
    load_dotenv()
    
    # Get project root directory
    project_root = Path(__file__).parent
    
    # Read manifest template
    template_path = project_root / "frontend" / "manifest.template.json"
    output_path = project_root / "frontend" / "manifest.json"
    
    if not template_path.exists():
        print(f"Error: Template file not found {template_path}")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Replace environment variables
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            print("Error: GOOGLE_CLIENT_ID environment variable not found")
            print("Please ensure .env file exists and contains correct configuration")
            return False
        
        manifest['oauth2']['client_id'] = client_id
        
        # Write final file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Successfully generated {output_path}")
        print(f"Using Client ID: {client_id[:20]}...")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if build_manifest():
        print("Build completed!")
    else:
        print("Build failed!")
        exit(1)
