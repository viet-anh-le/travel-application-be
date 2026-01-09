import sys, os, io, re
import onnxruntime as ort
import numpy as np
import torch
import torchaudio

# Cache for ONNX sessions keyed by (encoder,decoder,joiner) paths
_sessions_cache = {}

def silent_session(model_path):
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    so = ort.SessionOptions()
    so.log_severity_level = 4
    ort.set_default_logger_severity(4)

    sess = ort.InferenceSession(model_path, sess_options=so,
                                providers=["CPUExecutionProvider"])

    sys.stdout, sys.stderr = old_stdout, old_stderr
    return sess


def stt_transcribe(
        audio_bytes: bytes,
        encoder_path="models/encoder-epoch-20-avg-10.onnx",
        decoder_path="models/decoder-epoch-20-avg-10.onnx",
        joiner_path="models/joiner-epoch-20-avg-10.onnx",
):
    sample_rate = 16000
    # Chuyển bytes sang numpy float32, chuẩn hóa [-1,1]
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    waveform = torch.from_numpy(audio_np).unsqueeze(0)  # shape (1, N)

    # mel spectrogram
    mel = torchaudio.transforms.MelSpectrogram(
        sample_rate=sample_rate,
        n_fft=400,
        hop_length=160,
        win_length=400,
        f_min=20,
        f_max=sample_rate / 2,
        n_mels=80,
        power=2.0,
    )(waveform)

    log_mel = torch.clamp(mel, min=1e-10).log()
    features = log_mel.squeeze(0).transpose(0, 1).numpy().astype(np.float32)
    T = features.shape[0]

    base_dir = os.path.dirname(__file__)
    encoder_path = os.path.join(base_dir, encoder_path)
    decoder_path = os.path.join(base_dir, decoder_path)
    joiner_path = os.path.join(base_dir, joiner_path)

    # Try to reuse ONNX sessions to avoid reloading models on every call (very slow)
    global _sessions_cache
    cache_key = (encoder_path, decoder_path, joiner_path)
    if cache_key in _sessions_cache:
        encoder_sess, decoder_sess, joiner_sess = _sessions_cache[cache_key]
    else:
        encoder_sess = silent_session(encoder_path)
        decoder_sess = silent_session(decoder_path)
        joiner_sess = silent_session(joiner_path)
        _sessions_cache[cache_key] = (encoder_sess, decoder_sess, joiner_sess)

    encoder_in = np.expand_dims(features, 0)
    x_lens = np.array([T], dtype=np.int64)

    encoder_out, _ = encoder_sess.run(None, {"x": encoder_in, "x_lens": x_lens})
    encoder_out = encoder_out[0]  # (T,512)

    y = [0, 0]
    result = []

    for t in range(encoder_out.shape[0]):
        enc_frame = encoder_out[t:t + 1]

        while True:
            dec_in = np.array([y[-2:]], dtype=np.int64)
            dec_out = decoder_sess.run(None, {"y": dec_in})[0]
            join_out = joiner_sess.run(None, {
                "encoder_out": enc_frame.astype(np.float32),
                "decoder_out": dec_out.astype(np.float32)
            })[0]

            token = int(np.argmax(join_out, axis=-1)[0])
            if token == 0:
                break

            result.append(token)
            y.append(token)

    # decode tokens
    config_path = os.path.join(base_dir, "models/config.json")
    if not os.path.exists(config_path):
        return "Missing token config.json"

    def load_tok(path):
        arr = []
        with open(path, "r", encoding="utf8") as f:
            for line in f:
                parts = line.strip().split()
                tok = parts[0]
                arr.append(tok)
        return arr

    tokens = load_tok(config_path)
    text = "".join(tokens[i] for i in result if i < len(tokens))
    text = text.replace("▁", " ")
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text
