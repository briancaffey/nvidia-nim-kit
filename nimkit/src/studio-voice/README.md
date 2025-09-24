# NVIDIA Studio Voice NIM Client

This package has a sample client which demonstrates interaction with a Studio Voice NIM.

## Getting Started

NVIDIA Maxine NIM Client packages use gRPC APIs. Instructions below demonstrate usage of Studio Voice NIM using Python gRPC client.
Additionally, access the [Try API](https://build.nvidia.com/nvidia/studiovoice/api) feature to experience the NVIDIA Studio Voice NIM API without hosting your own servers, as it leverages the NVIDIA Cloud Functions backend.

## Pre-requisites

- Ensure you have Python 3.10 or above installed on your system.
Please refer to the [Python documentation](https://www.python.org/downloads/) for download and installation instructions.
- Access to NVIDIA Studio Voice NIM Container / Service.

## Usage guide

### 1. Clone the repository

```bash
git clone https://github.com/nvidia-maxine/nim-clients.git

// Go to the 'studio-voice' folder
cd nim-clients/studio-voice
```

### 2. Install Dependencies

```bash
sudo apt-get install python3-pip
pip install -r requirements.txt
```

### 3. Host the NIM Server

Before running client part of Studio Voice, please set up a server.
The simplest way to do that is to follow the [quick start guide](https://docs.nvidia.com/nim/maxine/studio-voice/latest/index.html).
This step can be skipped when using [Try API](https://build.nvidia.com/nvidia/studiovoice/api).


### 4. Compile the Protos

Before running the python client, you can choose to compile the protos.
The grpcio version needed for compilation can be referred at requirements.txt

To compile protos on Linux, run:
```bash
// Go to studio-voice/protos folder
cd studio-voice/protos

chmod +x compile_protos.sh
./compile_protos.sh
```

To compile protos on Windows, run:
```bash
// Go to studio-voice/protos folder
cd studio-voice/protos

compile_protos.bat
```

### 5. Run the Python Client

Go to the scripts directory.

```bash
cd scripts
```

#### Usage for Transactional NIM Request

To run client in transactional mode. Set `--model-type` in accordance with the server, default is set to `48k-hq`. The following example command processes the packaged sample audio file in transactional mode and generates a `studio_voice_48k_output.wav` file in the current folder.

```bash
python studio_voice.py --target 127.0.0.1:8001 --input ../assets/studio_voice_48k_input.wav --output studio_voice_48k_output.wav --model-type 48k-hq
```

```
python studio_voice.py --target 192.168.5.173:8001 --input ../assets/studio_voice_48k_input.wav --output studio_voice_48k_output.wav --model-type 48k-hq
```

#### Usage for Streaming NIM Request

To run the client in streaming mode, add `--streaming`. The following example command processes the packaged sample audio file in streaming mode and generates a `studio_voice_48k_output.wav` file in the current folder.

```bash
python studio_voice.py --target 127.0.0.1:8001 --input ../assets/studio_voice_48k_input.wav --output studio_voice_48k_output.wav --streaming --model-type 48k-ll
```

Only WAV files are supported.

#### Usage for Preview API Request

```bash
python studio_voice.py --preview-mode \
    --ssl-mode TLS \
    --target grpc.nvcf.nvidia.com:443 \
    --function-id <function_id> \
    --api-key $API_KEY_REQUIRED_IF_EXECUTING_OUTSIDE_NGC \
    --input <input_file_path> \
    --output <output_file_path> \
```

#### Command Line Arguments

- `--preview-mode`  - Flag to send request to preview NVCF server on https://build.nvidia.com/nvidia/studiovoice/api.
- `--ssl-mode`      - Flag to control if SSL MTLS/TLS encryption should be used. When running preview SSL must be set to TLS. Default value is `None`.
- `--ssl-key`       - The path to ssl private key. Default value is `None`.
- `--ssl-cert`      - The path to ssl certificate chain. Default value is `None`.
- `--ssl-root-cert` - The path to ssl root certificate. Default value is `None`.
- `--target`        - <IP:port> of gRPC service, when hosted locally. Use grpc.nvcf.nvidia.com:443 when hosted on NVCF.
- `--api-key`       - NGC API key required for authentication, utilized when using `TRY API` ignored otherwise.
- `--function-id`   - NVCF function ID for the service, utilized when using `TRY API` ignored otherwise.
- `--input`         - The path to the input audio file. Default value is `../assets/studio_voice_48k_input.wav`.
- `--output`        - The path for the output audio file. Default is current directory (scripts) with name `studio_voice_48k_output.wav`.
- `--streaming`     - Flag to control if streaming mode should be used. Transactional mode will be used by default.
- `--model-type`    - Studio Voice model type hosted on server. It can be set to `48k-hq/48k-ll/16k-hq`. Default value is `48k-hq`.

Refer the [docs](https://docs.nvidia.com/nim/maxine/studio-voice/latest/index.html) for more information.
