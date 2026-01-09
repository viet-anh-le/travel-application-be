import argparse
import time

import sherpa_onnx
import soundfile as sf


def add_vits_args(parser):
    parser.add_argument(
        "--vits-model",
        type=str,
        default="",
        help="Path to vits model.onnx",
    )

    parser.add_argument(
        "--vits-lexicon",
        type=str,
        default="",
        help="Path to lexicon.txt",
    )

    parser.add_argument(
        "--vits-tokens",
        type=str,
        default="",
        help="Path to tokens.txt",
    )

    parser.add_argument(
        "--vits-data-dir",
        type=str,
        default="",
        help="""Path to the dict directory of espeak-ng. If it is specified,
        --vits-lexicon and --vits-tokens are ignored""",
    )


def add_matcha_args(parser):
    parser.add_argument(
        "--matcha-acoustic-model",
        type=str,
        default="",
        help="Path to model.onnx for matcha",
    )

    parser.add_argument(
        "--matcha-vocoder",
        type=str,
        default="",
        help="Path to vocoder for matcha",
    )

    parser.add_argument(
        "--matcha-lexicon",
        type=str,
        default="",
        help="Path to lexicon.txt for matcha",
    )

    parser.add_argument(
        "--matcha-tokens",
        type=str,
        default="",
        help="Path to tokens.txt for matcha",
    )

    parser.add_argument(
        "--matcha-data-dir",
        type=str,
        default="",
        help="""Path to the dict directory of espeak-ng. If it is specified,
        --matcha-lexicon and --matcha-tokens are ignored""",
    )


def add_kokoro_args(parser):
    parser.add_argument(
        "--kokoro-model",
        type=str,
        default="",
        help="Path to model.onnx for kokoro",
    )

    parser.add_argument(
        "--kokoro-voices",
        type=str,
        default="",
        help="Path to voices.bin for kokoro",
    )

    parser.add_argument(
        "--kokoro-tokens",
        type=str,
        default="",
        help="Path to tokens.txt for kokoro",
    )

    parser.add_argument(
        "--kokoro-data-dir",
        type=str,
        default="",
        help="Path to the dict directory of espeak-ng.",
    )

    parser.add_argument(
        "--kokoro-lexicon",
        type=str,
        default="",
        help="Path to lexicon.txt for kokoro. Needed only by multilingual kokoro",
    )


def add_kitten_args(parser):
    parser.add_argument(
        "--kitten-model",
        type=str,
        default="",
        help="Path to model.onnx for kitten",
    )

    parser.add_argument(
        "--kitten-voices",
        type=str,
        default="",
        help="Path to voices.bin for kitten",
    )

    parser.add_argument(
        "--kitten-tokens",
        type=str,
        default="",
        help="Path to tokens.txt for kitten",
    )

    parser.add_argument(
        "--kitten-data-dir",
        type=str,
        default="",
        help="Path to the dict directory of espeak-ng.",
    )


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    add_vits_args(parser)
    add_matcha_args(parser)
    add_kokoro_args(parser)
    add_kitten_args(parser)

    parser.add_argument(
        "--tts-rule-fsts",
        type=str,
        default="",
        help="Path to rule.fst",
    )

    parser.add_argument(
        "--max-num-sentences",
        type=int,
        default=1,
        help="""Max number of sentences in a batch to avoid OOM if the input
        text is very long. Set it to -1 to process all the sentences in a
        single batch. A smaller value does not mean it is slower compared
        to a larger one on CPU.
        """,
    )

    parser.add_argument(
        "--output-filename",
        type=str,
        default="./generated.wav",
        help="Path to save generated wave",
    )

    parser.add_argument(
        "--sid",
        type=int,
        default=0,
        help="""Speaker ID. Used only for multi-speaker models, e.g.
        models trained using the VCTK dataset. Not used for single-speaker
        models, e.g., models trained using the LJ speech dataset.
        """,
    )

    parser.add_argument(
        "--debug",
        type=bool,
        default=False,
        help="True to show debug messages",
    )

    parser.add_argument(
        "--provider",
        type=str,
        default="cpu",
        help="valid values: cpu, cuda, coreml",
    )

    parser.add_argument(
        "--num-threads",
        type=int,
        default=1,
        help="Number of threads for neural network computation",
    )

    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        help="Speech speed. Larger->faster; smaller->slower",
    )

    parser.add_argument(
        "text",
        type=str,
        help="The input text to generate audio for",
    )

    return parser.parse_args()


def main():
    args = get_args()
    print(args)

    tts_config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=args.vits_model,
                lexicon=args.vits_lexicon,
                data_dir=args.vits_data_dir,
                tokens=args.vits_tokens,
            ),
            matcha=sherpa_onnx.OfflineTtsMatchaModelConfig(
                acoustic_model=args.matcha_acoustic_model,
                vocoder=args.matcha_vocoder,
                lexicon=args.matcha_lexicon,
                tokens=args.matcha_tokens,
                data_dir=args.matcha_data_dir,
            ),
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=args.kokoro_model,
                voices=args.kokoro_voices,
                tokens=args.kokoro_tokens,
                data_dir=args.kokoro_data_dir,
                lexicon=args.kokoro_lexicon,
            ),
            kitten=sherpa_onnx.OfflineTtsKittenModelConfig(
                model=args.kitten_model,
                voices=args.kitten_voices,
                tokens=args.kitten_tokens,
                data_dir=args.kitten_data_dir,
            ),
            provider=args.provider,
            debug=args.debug,
            num_threads=args.num_threads,
        ),
        rule_fsts=args.tts_rule_fsts,
        max_num_sentences=args.max_num_sentences,
    )
    if not tts_config.validate():
        raise ValueError("Please check your config")

    tts = sherpa_onnx.OfflineTts(tts_config)

    start = time.time()
    audio = tts.generate(args.text, sid=args.sid, speed=args.speed)
    end = time.time()

    if len(audio.samples) == 0:
        print("Error in generating audios. Please read previous error messages.")
        return

    elapsed_seconds = end - start
    audio_duration = len(audio.samples) / audio.sample_rate
    real_time_factor = elapsed_seconds / audio_duration

    sf.write(
        args.output_filename,
        audio.samples,
        samplerate=audio.sample_rate,
        subtype="PCM_16",
    )

if __name__ == "__main__":
    main()