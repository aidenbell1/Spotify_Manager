import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import argparse
import sys
import os
from typing import List, Dict, Optional

# Import configuration
try:
    import config
except ImportError:
    print("❌ Error: config.py file not found!")
    print("Please create a config.py file with your Spotify credentials.")
    print("See config.py.example for the required format.")
    sys.exit(1)


class SpotifyManager:
    """Manages Spotify liked songs and top tracks with rate limiting."""
    
    def __init__(self, batch_size: int = None, delay: float = None):
        """
        Initialize Spotify Manager with config file credentials.
        
        Args:
            batch_size: Number of songs to process at once (default from config)
            delay: Seconds to wait between API calls (default from config)
        """
        # Validate required config
        required_configs = ['CLIENT_ID', 'CLIENT_SECRET', 'REDIRECT_URI', 'SCOPES']
        for conf in required_configs:
            if not hasattr(config, conf) or not getattr(config, conf):
                raise ValueError(f"Missing required config: {conf}")
        
        # Set up API client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=config.CLIENT_ID,
            client_secret=config.CLIENT_SECRET,
            redirect_uri=config.REDIRECT_URI,
            scope=config.SCOPES
        ))
        
        # Set processing parameters
        self.batch_size = batch_size or getattr(config, 'DEFAULT_BATCH_SIZE', 20)
        self.delay = delay or getattr(config, 'DEFAULT_DELAY', 0.5)
        self.error_delay = getattr(config, 'ERROR_RETRY_DELAY', 60)
        
        print(f"✅ Connected to Spotify API")
        print(f"⚙️ Batch size: {self.batch_size}, Delay: {self.delay}s")
    
    def get_user_info(self) -> Dict:
        """Get current user information."""
        try:
            user = self.sp.current_user()
            return {
                'name': user['display_name'],
                'followers': user['followers']['total'],
                'id': user['id']
            }
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            return {}
    
    def get_top_tracks(self, time_range: str = 'medium_term', limit: int = 50) -> Dict:
        """
        Get user's top tracks with pagination.
        
        Args:
            time_range: 'short_term', 'medium_term', or 'long_term'
            limit: Maximum number of tracks per request (Spotify max: 50)
        
        Returns:
            Dictionary with 'items' list containing track info
        """
        all_top_tracks = []
        offset = 0
        
        print(f"📈 Fetching top tracks ({time_range})...")
        
        while True:
            try:
                top_tracks = self.sp.current_user_top_tracks(
                    time_range=time_range, 
                    limit=limit, 
                    offset=offset
                )
                
                batch_items = top_tracks['items']
                all_top_tracks.extend(batch_items)
                
                print(f"  Got {len(batch_items)} tracks (total: {len(all_top_tracks)})")
                
                if len(batch_items) < limit:
                    break
                    
                offset += limit
                time.sleep(self.delay)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error fetching top tracks: {e}")
                break
        
        # Format the results
        formatted_tracks = []
        for i, track in enumerate(all_top_tracks):
            formatted_tracks.append({
                'index': i + 1,
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'id': track['id'],
                'popularity': track.get('popularity', 0)
            })
        
        print(f"✅ Found {len(formatted_tracks)} top tracks")
        return {'items': formatted_tracks}
    
    def get_liked_songs(self) -> Dict:
        """
        Get all user's liked songs with pagination.
        
        Returns:
            Dictionary with 'items' list containing track info
        """
        all_liked_songs = []
        offset = 0
        limit = 50
        
        print("❤️ Fetching liked songs...")
        
        while True:
            try:
                liked_songs = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
                batch_items = liked_songs['items']
                all_liked_songs.extend(batch_items)
                
                print(f"  Got {len(batch_items)} songs (total: {len(all_liked_songs)})")
                
                if len(batch_items) < limit:
                    break
                    
                offset += limit
                time.sleep(self.delay)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Error fetching liked songs: {e}")
                break
        
        # Format the results
        formatted_songs = []
        for i, item in enumerate(all_liked_songs):
            track = item['track']
            if track:  # Sometimes tracks can be None if removed from Spotify
                formatted_songs.append({
                    'index': i + 1,
                    'name': track['name'],
                    'artists': ', '.join([artist['name'] for artist in track['artists']]),
                    'id': track['id'],
                    'added_at': item['added_at']
                })
        
        print(f"✅ Found {len(formatted_songs)} liked songs")
        return {'items': formatted_songs}
    
    def _process_in_batches(self, track_ids: List[str], action: str, api_method) -> bool:
        """
        Process track IDs in batches with rate limiting.
        
        Args:
            track_ids: List of Spotify track IDs
            action: Description of the action for logging
            api_method: The Spotify API method to call
        
        Returns:
            True if successful, False if there were errors
        """
        if not track_ids:
            print(f"No tracks to {action.lower()}.")
            return True
        
        print(f"{action} {len(track_ids)} tracks in batches of {self.batch_size}...")
        
        success_count = 0
        error_count = 0
        
        for i in range(0, len(track_ids), self.batch_size):
            batch = track_ids[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            try:
                api_method(batch)
                success_count += len(batch)
                print(f"✅ {action} batch {batch_num} ({len(batch)} songs)")
                
                # Rate limiting delay
                if i + self.batch_size < len(track_ids):  # Don't wait after last batch
                    time.sleep(self.delay)
                    
            except Exception as e:
                error_count += len(batch)
                print(f"❌ Error in batch {batch_num}: {e}")
                print(f"⏰ Waiting {self.error_delay} seconds before continuing...")
                time.sleep(self.error_delay)
        
        print(f"📊 Results: {success_count} successful, {error_count} failed")
        return error_count == 0
    
    def clear_liked_songs(self, track_ids: Optional[List[str]] = None) -> bool:
        """
        Clear liked songs safely in batches.
        
        Args:
            track_ids: Specific track IDs to remove. If None, removes all liked songs.
        
        Returns:
            True if successful
        """
        if track_ids is None:
            # Get all liked songs
            liked_songs = self.get_liked_songs()
            track_ids = [item['id'] for item in liked_songs['items']]
        
        return self._process_in_batches(
            track_ids, 
            "🗑️ Removing", 
            self.sp.current_user_saved_tracks_delete
        )
    
    def add_liked_songs(self, track_ids: List[str]) -> bool:
        """
        Add tracks to liked songs safely in batches.
        
        Args:
            track_ids: List of Spotify track IDs to add
        
        Returns:
            True if successful
        """
        return self._process_in_batches(
            track_ids,
            "➕ Adding",
            self.sp.current_user_saved_tracks_add
        )
    
    def replace_liked_with_top(self, time_range: str = 'medium_term', limit: int = 50, dry_run: bool = False) -> bool:
        """
        Replace all liked songs with top tracks.
        
        Args:
            time_range: Time range for top tracks
            limit: Number of top tracks to get
            dry_run: If True, show what would happen without making changes
        
        Returns:
            True if successful
        """
        print("🎵 Starting liked songs replacement...")
        
        # Get user info
        user_info = self.get_user_info()
        if user_info:
            print(f"👤 User: {user_info['name']} ({user_info['followers']} followers)")
        
        # Get top tracks
        top_tracks = self.get_top_tracks(time_range=time_range, limit=limit)
        top_track_ids = [item['id'] for item in top_tracks['items']]
        
        if not top_track_ids:
            print("❌ No top tracks found!")
            return False
        
        if dry_run:
            print(f"\n🔍 DRY RUN - Would replace liked songs with these {len(top_track_ids)} tracks:")
            for track in top_tracks['items'][:10]:  # Show first 10
                print(f"  {track['index']}. {track['name']} by {track['artists']}")
            if len(top_tracks['items']) > 10:
                print(f"  ... and {len(top_tracks['items']) - 10} more")
            return True
        
        # Clear current liked songs
        print("\n🗑️ Clearing current liked songs...")
        if not self.clear_liked_songs():
            print("❌ Failed to clear liked songs!")
            return False
        
        # Add top tracks
        print("\n➕ Adding top tracks to liked songs...")
        if not self.add_liked_songs(top_track_ids):
            print("❌ Failed to add top tracks!")
            return False
        
        print("✅ Successfully replaced liked songs with top tracks!")
        return True


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description='Manage Spotify liked songs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""" Examples:
        python spotify_manager.py                    # Replace liked songs with top 50 tracks
        python spotify_manager.py --limit 20         # Use only top 20 tracks
        python spotify_manager.py --time-range short # Use last 4 weeks instead of 6 months
        python spotify_manager.py --dry-run          # See what would happen without changes
        python spotify_manager.py --show-top         # Just show your top tracks
        python spotify_manager.py --show-liked       # Just show your liked songs
        """
    )
    
    parser.add_argument('--limit', type=int, default=50, help='Number of top tracks to get (default: 50)')
    parser.add_argument('--time-range', choices=['short', 'medium', 'long'], default='short', help='Time range: short (4 weeks), medium (6 months), long (years)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would happen without making changes')
    parser.add_argument('--show-top', action='store_true', help='Just show your top tracks')
    parser.add_argument('--show-liked', action='store_true', help='Just show your liked songs')
    parser.add_argument('--batch-size', type=int, default=None, help='Number of songs to process at once (default from config)')
    
    args = parser.parse_args()
    
    # Convert time range to Spotify format
    time_range_map = getattr(config, 'TIME_RANGES', {
        'short': 'short_term',
        'medium': 'medium_term', 
        'long': 'long_term'
    })
    spotify_time_range = time_range_map.get(args.time_range, 'medium_term')
    
    try:
        # Initialize Spotify Manager
        manager = SpotifyManager(batch_size=args.batch_size)
        
        # Handle different actions
        if args.show_top:
            top_tracks = manager.get_top_tracks(time_range=spotify_time_range, limit=args.limit)
            print(f"\n📈 Your Top {len(top_tracks['items'])} Tracks:")
            for track in top_tracks['items']:
                print(f"  {track['index']}. {track['name']} by {track['artists']}")
                
        elif args.show_liked:
            liked_songs = manager.get_liked_songs()
            print(f"\n❤️ Your {len(liked_songs['items'])} Liked Songs:")
            for song in liked_songs['items'][:20]:  # Show first 20
                print(f"  {song['index']}. {song['name']} by {song['artists']}")
            if len(liked_songs['items']) > 20:
                print(f"  ... and {len(liked_songs['items']) - 20} more")
                
        else:
            # Replace liked songs with top tracks
            success = manager.replace_liked_with_top(
                time_range=spotify_time_range,
                limit=args.limit,
                dry_run=args.dry_run
            )
            
            if not success:
                sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()