#!/usr/bin/env python3
"""
Audio sample rate converter utility.
Converts audio files to different sample rates using soundfile library.
"""

import argparse
import os
import soundfile as sf
import numpy as np


def convert_sample_rate(input_file, output_file, target_sample_rate):
    """
    Convert audio file to target sample rate.

    Args:
        input_file (str): Path to input audio file
        output_file (str): Path to output audio file
        target_sample_rate (int): Target sample rate in Hz
    """
    # Read the input file
    print(f"Reading audio file: {input_file}")
    data, sample_rate = sf.read(input_file)

    print(f"Original sample rate: {sample_rate} Hz")
    print(f"Target sample rate: {target_sample_rate} Hz")
    print(f"Audio duration: {len(data) / sample_rate:.2f} seconds")

    # Convert sample rate
    # Calculate the ratio for resampling
    ratio = target_sample_rate / sample_rate

    # Simple linear interpolation for resampling
    # For better quality, you might want to use scipy.signal.resample
    new_length = int(len(data) * ratio)
    resampled_data = np.interp(
        np.linspace(0, len(data), new_length), np.arange(len(data)), data
    )

    # Write the output file
    print(f"Writing output file: {output_file}")
    sf.write(output_file, resampled_data, target_sample_rate)

    print(f"Conversion complete! Output saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Convert audio file sample rate")
    parser.add_argument("--input", "-i", required=True, help="Input audio file path")
    parser.add_argument("--output", "-o", required=True, help="Output audio file path")
    parser.add_argument(
        "--sample-rate",
        "-s",
        type=int,
        default=48000,
        help="Target sample rate (default: 48000)",
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' does not exist.")
        return 1

    try:
        convert_sample_rate(args.input, args.output, args.sample_rate)
        return 0
    except Exception as e:
        print(f"Error during conversion: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
