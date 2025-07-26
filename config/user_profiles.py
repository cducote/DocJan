"""
User profile management for DocJanitor.
Handles local storage of user settings with encryption.
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime

class UserProfileManager:
    """Manages user profiles with local JSON storage"""
    
    def __init__(self, profiles_file=".user_profiles.json"):
        self.profiles_file = profiles_file
        self.profiles = self._load_profiles()
    
    def _load_profiles(self) -> Dict:
        """Load profiles from JSON file"""
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load profiles file: {e}")
                return {}
        return {}
    
    def save_profiles(self):
        """Save profiles to JSON file"""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except IOError as e:
            print(f"Error saving profiles: {e}")
    
    def add_profile(self, name: str, email: str, confluence_url: str, api_token: str, preferences: Dict = None):
        """Add or update a user profile"""
        # TODO: In future version, encrypt the API token
        self.profiles[name] = {
            'email': email,
            'confluence_url': confluence_url,
            'api_token': api_token,  # Will be encrypted in future version
            'preferences': preferences or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_used': True  # Set new/updated profile as active
        }
        
        # Set all other profiles to not last_used
        for profile_name in self.profiles:
            if profile_name != name:
                self.profiles[profile_name]['last_used'] = False
        
        self.save_profiles()
        return self.profiles[name]
    
    def get_profile(self, name: str) -> Optional[Dict]:
        """Get a specific profile by name"""
        return self.profiles.get(name)
    
    def get_last_used_profile(self) -> Optional[Dict]:
        """Get the profile that was last used"""
        for name, profile in self.profiles.items():
            if profile.get('last_used', False):
                profile['name'] = name
                return profile
        return None
    
    def list_profiles(self) -> List[str]:
        """Get list of all profile names"""
        return list(self.profiles.keys())
    
    def set_active_profile(self, name: str) -> bool:
        """Set a profile as active (last used)"""
        if name not in self.profiles:
            return False
        
        # Set all to False first
        for profile_name in self.profiles:
            self.profiles[profile_name]['last_used'] = False
        
        # Set selected to True and update timestamp
        self.profiles[name]['last_used'] = True
        self.profiles[name]['updated_at'] = datetime.now().isoformat()
        self.save_profiles()
        return True
    
    def delete_profile(self, name: str) -> bool:
        """Delete a profile"""
        if name in self.profiles:
            was_active = self.profiles[name].get('last_used', False)
            del self.profiles[name]
            
            # If we deleted the active profile, make the first remaining profile active
            if was_active and self.profiles:
                first_profile = next(iter(self.profiles))
                self.profiles[first_profile]['last_used'] = True
            
            self.save_profiles()
            return True
        return False
    
    def update_profile_preferences(self, name: str, preferences: Dict) -> bool:
        """Update preferences for a specific profile"""
        if name in self.profiles:
            self.profiles[name]['preferences'] = preferences
            self.profiles[name]['updated_at'] = datetime.now().isoformat()
            self.save_profiles()
            return True
        return False
    
    def get_profile_for_session_state(self, name: str) -> Optional[Dict]:
        """Get profile data formatted for Streamlit session state"""
        profile = self.get_profile(name)
        if profile:
            return {
                'profile_name': name,
                'current_user_email': profile['email'],
                'confluence_url': profile['confluence_url'],
                'api_token': profile['api_token'],
                'user_preferences': profile.get('preferences', {})
            }
        return None
