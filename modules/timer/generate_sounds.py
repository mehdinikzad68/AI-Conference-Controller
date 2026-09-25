"""
Sound Generation Utility

Generates simple alert sounds for the timer module.
Run this script to create warning_beep.wav and finished_beep.wav in the assets directory.

Usage:
    python modules/timer/generate_sounds.py
"""

import numpy as np
from pathlib import Path
import wave
import struct

def generate_beep(frequency: int, duration: float, sample_rate: int = 44100) -> bytes:
    """
    Generate a simple beep tone.
    
    Args:
        frequency: Frequency in Hz
        duration: Duration in seconds
        sample_rate: Sample rate (default 44100 Hz)
        
    Returns:
        Bytes data for WAV file
    """
    t = np.linspace(0, duration, int(sample_rate * duration))
    wave_data = np.sin(2 * np.pi * frequency * t)
    
    # Apply fade in/out to avoid clicks
    fade_samples = int(sample_rate * 0.01)  # 10ms fade
    if len(wave_data) > fade_samples * 2:
        wave_data[:fade_samples] *= np.linspace(0, 1, fade_samples)
        wave_data[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    # Convert to 16-bit integers
    wave_data = (wave_data * 32767).astype(np.int16)
    
    # Convert to bytes
    return wave_data.tobytes()

def create_wav_file(filename: Path, wave_data: bytes, sample_rate: int = 44100):
    """
    Create a WAV file from wave data.
    
    Args:
        filename: Path to output WAV file
        wave_data: Raw wave data bytes
        sample_rate: Sample rate in Hz
    """
    with wave.open(str(filename), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave_data)

def main():
    """Generate alert sound files."""
    # Get assets directory
    assets_dir = Path(__file__).parent.parent.parent / "assets"
    assets_dir.mkdir(exist_ok=True)
    
    print("Generating alert sounds...")
    
    # Generate warning beep (higher pitch, double beep)
    print("  Creating warning_beep.wav...")
    beep1 = generate_beep(800, 0.2)  # First beep
    silence = np.zeros(int(44100 * 0.1), dtype=np.int16).tobytes()  # 100ms silence
    beep2 = generate_beep(800, 0.2)  # Second beep
    warning_data = beep1 + silence + beep2
    
    warning_path = assets_dir / "warning_beep.wav"
    create_wav_file(warning_path, warning_data)
    print(f"    ✓ Created {warning_path}")
    
    # Generate finished beep (lower pitch, triple beep)
    print("  Creating finished_beep.wav...")
    beep1 = generate_beep(600, 0.3)  # First beep
    silence = np.zeros(int(44100 * 0.1), dtype=np.int16).tobytes()  # 100ms silence
    beep2 = generate_beep(600, 0.3)  # Second beep
    silence2 = np.zeros(int(44100 * 0.1), dtype=np.int16).tobytes()
    beep3 = generate_beep(600, 0.3)  # Third beep
    finished_data = beep1 + silence + beep2 + silence2 + beep3
    
    finished_path = assets_dir / "finished_beep.wav"
    create_wav_file(finished_path, finished_data)
    print(f"    ✓ Created {finished_path}")
    
    print("\n✓ All sound files generated successfully!")
    print(f"  Location: {assets_dir}")
    print("\nNote: You can replace these with custom sound files if desired.")

if __name__ == "__main__":
    main()

