# Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import argparse
import os
import sys
import grpc
import time
import soundfile as sf
import numpy as np
from typing import Iterator

sys.path.append(os.path.join(os.getcwd(), "../interfaces/studio_voice"))
# Importing gRPC compiler auto-generated maxine studiovoice library
import studiovoice_pb2  # noqa: E402
import studiovoice_pb2_grpc  # noqa: E402


def read_file_content(file_path: os.PathLike) -> None:
    """Function to read file content as bytes.

    Args:
      file_path: Path to input file
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist. Exiting.")

    with open(file_path, "rb") as file:
        return file.read()


def generate_request_for_inference(
    input_filepath: os.PathLike, model_type: str, sample_rate: int, streaming: bool
) -> None:
    """Generator to produce the request data stream

    Args:
      input_filepath: Path to input file
      model_type: Studio Voice model type to infer
      sample_rate: Input audio sample rate
      streaming: Enables grpc streaming mode
    """
    if streaming:
        """
        Input audio chunk is generated based on model type and sample rate,
        1) High quality models require 6sec input
        2) Low latency models require 10ms input chunk
        """
        input_audio, sample_rate_file = sf.read(input_filepath)
        input_audio = input_audio.astype(np.float32)  # Convert to float32
        input_size_in_ms = 10 if (model_type == "48k-ll") else 6000
        samples_per_ms = sample_rate // 1000
        input_float_size = int(input_size_in_ms * samples_per_ms)

        pad_length = input_float_size - len(input_audio) % input_float_size
        input_audio = np.pad(input_audio, (0, pad_length), "constant")

        print(
            f"Len {len(input_audio)}, chunk_size {input_float_size}, audio {input_audio}, "
            "type {input_audio.dtype}"
        )
        for i in range(0, len(input_audio), input_float_size):
            data = input_audio[i : i + input_float_size]
            yield studiovoice_pb2.EnhanceAudioRequest(audio_stream_data=data.tobytes())
    else:
        DATA_CHUNKS = 64 * 1024  # bytes, we send the wav file in 64KB chunks
        with open(input_filepath, "rb") as fd:
            while True:
                buffer = fd.read(DATA_CHUNKS)
                if buffer == b"":
                    break
                yield studiovoice_pb2.EnhanceAudioRequest(audio_stream_data=buffer)


def write_output_file_from_response(
    response_iter: Iterator[studiovoice_pb2.EnhanceAudioResponse],
    output_filepath: os.PathLike,
    sample_rate: int,
    streaming: bool,
) -> None:
    """Function to write the output file from the incoming gRPC data stream.

    Args:
      response_iter: Responses from the server to write into output file
      output_filepath: Path to output file
      sample_rate: Input audio sample rate
      streaming: Enables grpc streaming mode
    """
    if streaming:
        output_audio = []
        response_count = 0
        for response in response_iter:
            response_count += 1
            output_audio.append(np.frombuffer(response.audio_stream_data, np.float32))

        sf.write(output_filepath, np.hstack(output_audio), sample_rate)
        return response_count
    else:
        with open(output_filepath, "wb") as fd:
            for response in response_iter:
                if response.HasField("audio_stream_data"):
                    fd.write(response.audio_stream_data)


def parse_args() -> None:
    """
    Parse command-line arguments using argparse.
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Process wav audio files using gRPC and apply studio-voice."
    )
    parser.add_argument(
        "--preview-mode",
        action="store_true",
        help="Flag to send request to preview NVCF NIM server on "
        "https://build.nvidia.com/nvidia/studiovoice/api. ",
    )
    parser.add_argument(
        "--ssl-mode",
        type=str,
        help="Flag to set SSL mode, default is None",
        default=None,
        choices=["MTLS", "TLS"],
    )
    parser.add_argument(
        "--ssl-key",
        type=str,
        default=None,
        help="The path to ssl private key.",
    )
    parser.add_argument(
        "--ssl-cert",
        type=str,
        default=None,
        help="The path to ssl certificate chain.",
    )
    parser.add_argument(
        "--ssl-root-cert",
        type=str,
        default=None,
        help="The path to ssl root certificate.",
    )
    parser.add_argument(
        "--target",
        type=str,
        default="127.0.0.1:8001",
        help="IP:port of gRPC service, when hosted locally. "
        "Use grpc.nvcf.nvidia.com:443 when hosted on NVCF.",
    )
    parser.add_argument(
        "--input",
        type=str,
        default="../assets/studio_voice_48k_input.wav",
        help="The path to the input audio file.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="studio_voice_48k_output.wav",
        help="The path for the output audio file.",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="NGC API key required for authentication, "
        "utilized when using TRY API ignored otherwise",
    )
    parser.add_argument(
        "--function-id",
        type=str,
        help="NVCF function ID for the service, utilized when using TRY API ignored otherwise",
    )
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Flag to enable grpc streaming mode. ",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        help="Studio Voice model type, default is 48k-hq. ",
        default="48k-hq",
        choices=["48k-hq", "48k-ll", "16k-hq"],
    )
    return parser.parse_args()


def process_request(
    channel: any,
    input_filepath: os.PathLike,
    output_filepath: os.PathLike,
    model_type: str,
    sample_rate: int,
    streaming: bool,
    request_metadata: dict = None,
) -> None:
    """Function to process gRPC request

    Args:
      channel: gRPC channel for server client communication
      input_filepath: Path to input file
      output_filepath: Path to output file
      model_type: Studio Voice model type to infer
      sample_rate: Input audio sample rate
      streaming: Enables grpc streaming mode
      request_metadata: Credentials to process request
    """
    try:
        stub = studiovoice_pb2_grpc.MaxineStudioVoiceStub(channel)
        start_time = time.time()

        responses = stub.EnhanceAudio(
            generate_request_for_inference(
                input_filepath=input_filepath,
                model_type=model_type,
                sample_rate=sample_rate,
                streaming=streaming,
            ),
            metadata=request_metadata,
        )

        response_count = write_output_file_from_response(
            response_iter=responses,
            output_filepath=output_filepath,
            sample_rate=sample_rate,
            streaming=streaming,
        )

        end_time = time.time()
        if streaming:
            avg_latency = (end_time - start_time) / response_count
            print(f"Average latency per request: {avg_latency*1000:.2f}ms")
            print(f"Processed {response_count} chunks.")

        print(
            f"Function invocation completed in {end_time-start_time:.2f}s, "
            "the output file is generated."
        )
    except BaseException as e:
        print(e)


def main():
    """
    Main client function
    """
    args = parse_args()
    streaming = args.streaming
    model_type = args.model_type
    print(f"Streaming mode set to {streaming}")
    sample_rate = 48000
    if model_type == "16k-hq":
        sample_rate = 16000
    print(f"Sample Rate: {sample_rate}")
    input_filepath = args.input
    output_filepath = args.output

    # Check if input file path exists
    if os.path.isfile(input_filepath):
        print(f"The file '{input_filepath}' exists. Proceeding with processing.")
    else:
        raise FileNotFoundError(f"The file '{input_filepath}' does not exist. Exiting.")

    # Check the sample rate of the input audio file
    input_info = sf.info(input_filepath)
    input_sample_rate = input_info.samplerate
    print(f"Input file sample rate: {input_sample_rate}")

    # Check if the input file's sample rate matches the expected sample rate
    if input_sample_rate != sample_rate:
        raise ValueError(
            f"Sample rate mismatch: expected {sample_rate}, got {input_sample_rate}."
        )

    if args.preview_mode:
        if args.ssl_mode != "TLS":
            # Preview mode only supports TLS mode
            args.ssl_mode = "TLS"
            print("--ssl-mode is set as TLS, since preview_mode is enabled.")
        if args.ssl_root_cert:
            raise RuntimeError("Preview mode does not support custom root certificate.")

    if args.ssl_mode is not None:
        request_metadata = None
        root_certificates = None
        if args.ssl_mode == "MTLS":
            if not (args.ssl_key and args.ssl_cert and args.ssl_root_cert):
                raise RuntimeError(
                    "If --ssl-mode is MTLS, --ssl-key, --ssl-cert and --ssl-root-cert are required."
                )

            private_key = read_file_content(args.ssl_key)
            certificate_chain = read_file_content(args.ssl_cert)
            root_certificates = read_file_content(args.ssl_root_cert)
            channel_credentials = grpc.ssl_channel_credentials(
                root_certificates=root_certificates,
                private_key=private_key,
                certificate_chain=certificate_chain,
            )
        else:
            # Running with NVCF
            if args.preview_mode:
                request_metadata = (
                    ("authorization", "Bearer {}".format(args.api_key)),
                    ("function-id", args.function_id),
                )
                channel_credentials = grpc.ssl_channel_credentials()
            # Running TLS mode, without NVCF
            else:
                if not (args.ssl_root_cert):
                    raise RuntimeError(
                        "If --ssl-mode is TLS, --ssl-root-cert is required."
                    )
                root_certificates = read_file_content(args.ssl_root_cert)
                channel_credentials = grpc.ssl_channel_credentials(
                    root_certificates=root_certificates
                )

        with grpc.secure_channel(
            target=args.target, credentials=channel_credentials
        ) as channel:
            process_request(
                channel=channel,
                input_filepath=input_filepath,
                output_filepath=output_filepath,
                model_type=model_type,
                sample_rate=sample_rate,
                streaming=streaming,
                request_metadata=request_metadata,
            )
    else:
        with grpc.insecure_channel(target=args.target) as channel:
            process_request(
                channel=channel,
                input_filepath=input_filepath,
                output_filepath=output_filepath,
                model_type=model_type,
                sample_rate=sample_rate,
                streaming=streaming,
            )


if __name__ == "__main__":
    main()
